#!/usr/bin/env bash
set -Eeuo pipefail
cd "$HOME/tcc-bitemporal"
CONTAINER=tcc_postgres
DB=tcc_h3_update
DUMP="$HOME/backups/tcc_dominio_100k_base_20261003_1832.dump"
STAMP=$(date +%Y%m%d_%H%M%S)
OUT="evidencias/h3/update/lote_$STAMP"
mkdir -p "$OUT"
exec > >(tee -a "$OUT/execucao.log") 2>&1
trap 'echo "ERRO: linha $LINENO, codigo $?; conferir $OUT/execucao.log" >&2' ERR
N_CLIENTES=${N_CLIENTES:-8}
N_THREADS=${N_THREADS:-4}
N_TX=${N_TX:-100}
N_RODADAS=${N_RODADAS:-5}
N_AQUECIMENTO=${N_AQUECIMENTO:-100}
[[ -s "$DUMP" ]] || { echo 'Dump inexistente'; exit 1; }
[[ "$DB" == tcc_h3_update ]] || exit 1
[[ "$N_CLIENTES" =~ ^[0-9]+$ && "$N_THREADS" =~ ^[0-9]+$ && "$N_TX" =~ ^[0-9]+$ && "$N_RODADAS" =~ ^[0-9]+$ ]] || exit 1
for f in benchmark/bench_update_a.sql benchmark/bench_update_b.sql benchmark/analisar_pgbench.py; do [[ -s "$f" ]] || { echo "Falta $f"; exit 1; }; done
sha256sum "$DUMP" benchmark/bench_update_*.sql > "$OUT/sha256.txt"
podman exec "$CONTAINER" pg_isready -U dba -d postgres
podman exec "$CONTAINER" mkdir -p /tmp/h3
podman cp benchmark/bench_update_a.sql "$CONTAINER":/tmp/h3/bench_update_a.sql
podman cp benchmark/bench_update_b.sql "$CONTAINER":/tmp/h3/bench_update_b.sql
CSV="$OUT/resultados_update.csv"
echo 'modelo,rodada,transacoes,tps,media_ms,mediana_ms,p95_ms,min_ms,max_ms,desvio_padrao_ms' > "$CSV"
restaurar() {
  echo "Restaurando $DB..."
  local sessoes
  sessoes=$(podman exec "$CONTAINER" psql -X -U dba -d postgres -Atc "SELECT count(*) FROM pg_stat_activity WHERE datname='$DB'")
  [[ "$sessoes" == 0 ]] || { echo "ERRO: $sessoes sessoes conectadas"; exit 1; }
  podman exec "$CONTAINER" dropdb -U dba --if-exists "$DB"
  podman exec "$CONTAINER" createdb -U dba -T template0 "$DB"
  podman exec -i "$CONTAINER" pg_restore -U dba -d "$DB" --no-owner --no-privileges --exit-on-error --single-transaction < "$DUMP"
  local contagens
  contagens=$(podman exec "$CONTAINER" psql -X -U dba -d "$DB" -Atc "SELECT (SELECT count(*) FROM parte_controle),(SELECT count(*) FROM parte),(SELECT count(*) FROM parte_historico),(SELECT count(*) FROM parte WHERE valid_at @> DATE '2026-09-01')")
  [[ "$contagens" == '100000|115182|84427|100000' ]] || { echo "Baseline incorreto: $contagens"; exit 1; }
}
rodar() {
  local modelo=$1 rodada=$2 qt=$3 prefix=$4
  local script="/tmp/h3/bench_update_${modelo,,}.sql"
  local resultado="$OUT/${prefix}.txt"
  local logs="$OUT/${prefix}_TRANSACOES.log"
  echo "Executando $prefix; clientes=$N_CLIENTES, threads=$N_THREADS, transacoes/cliente=$qt"
  podman exec "$CONTAINER" sh -c "rm -f /tmp/h3/${prefix}.*"
  podman exec "$CONTAINER" pgbench -n -U dba -d "$DB" -c "$N_CLIENTES" -j "$N_THREADS" -t "$qt" -r -l --log-prefix="/tmp/h3/${prefix}" -f "$script" | tee "$resultado"
  podman exec "$CONTAINER" sh -c "cat /tmp/h3/${prefix}.*" > "$logs"
  local esperado=$((N_CLIENTES * qt))
  local obtido
  obtido=$(wc -l < "$logs")
  [[ "$obtido" -eq "$esperado" ]] || { echo "Log inconsistente: $obtido de $esperado"; exit 1; }
  grep -q 'number of failed transactions: 0 (0.000%)' "$resultado" || { echo 'Houve falhas'; exit 1; }
  local historico
  historico=$(podman exec "$CONTAINER" psql -X -U dba -d "$DB" -Atc 'SELECT count(*) FROM parte_historico')
  if [[ "$modelo" == B ]]; then
    [[ "$historico" -eq $((84427 + esperado)) ]] || { echo "Historico esperado $((84427+esperado)), obtido $historico"; exit 1; }
  else
    [[ "$historico" -eq 84427 ]] || { echo "Modelo A alterou historico: $historico"; exit 1; }
  fi
  echo "historico_depois=$historico" > "$OUT/${prefix}_VALIDACAO.txt"
  if [[ "$rodada" != 'warmup' ]]; then
    python3 benchmark/analisar_pgbench.py --log "$logs" --saida-pgbench "$resultado" --modelo "$modelo" --rodada "$rodada" >> "$CSV"
  fi
}
echo "Inicio: $(date -Iseconds)"
echo "Saida: $OUT"
echo "Rodadas oficiais: $N_RODADAS; transacoes por cliente: $N_TX"
for modelo in A B; do
  restaurar
  rodar "$modelo" warmup "$N_AQUECIMENTO" "UPDATE_${modelo}_WARMUP"
done
for rodada in $(seq 1 "$N_RODADAS"); do
  if ((rodada % 2 == 1)); then ordem='A B'; else ordem='B A'; fi
  for modelo in $ordem; do
    restaurar
    rodar "$modelo" "$rodada" "$N_TX" "UPDATE_${modelo}_R${rodada}"
  done
done
printf '\nRESULTADOS:\n'; cat "$CSV"
echo "Concluido em $(date -Iseconds); $OUT"
