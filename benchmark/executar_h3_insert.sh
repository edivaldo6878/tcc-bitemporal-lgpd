#!/usr/bin/env bash
set -Eeuo pipefail
cd "$HOME/tcc-bitemporal"
CONTAINER=tcc_postgres
DB=tcc_h3_update
DUMP="$HOME/backups/tcc_dominio_100k_base_20261003_1832.dump"
STAMP=$(date +%Y%m%d_%H%M%S)
OUT="evidencias/h3/insert/lote_$STAMP"
mkdir -p "$OUT"
exec > >(tee -a "$OUT/execucao.log") 2>&1
trap 'rc=$?; echo "ERRO: linha $LINENO, codigo $rc; conferir $OUT/execucao.log" >&2' ERR
N_CLIENTES=${N_CLIENTES:-8}
N_THREADS=${N_THREADS:-4}
N_TX=${N_TX:-100}
N_RODADAS=${N_RODADAS:-5}
N_AQUECIMENTO=${N_AQUECIMENTO:-100}
[[ -s "$DUMP" ]] || { echo 'ERRO: dump inexistente'; exit 1; }
[[ "$DB" == tcc_h3_update ]] || exit 1
for v in N_CLIENTES N_THREADS N_TX N_RODADAS N_AQUECIMENTO; do
  [[ "${!v}" =~ ^[0-9]+$ ]] && (( ${!v} > 0 )) || { echo "ERRO: $v invalido"; exit 1; }
done
(( N_THREADS <= N_CLIENTES )) || { echo 'ERRO: threads > clientes'; exit 1; }
(( N_CLIENTES * N_TX <= 80000 && N_CLIENTES * N_AQUECIMENTO <= 80000 )) || {
  echo 'ERRO: maximo de 80000 IDs por execucao'; exit 1;
}
for f in benchmark/bench_insert_a.sql benchmark/bench_insert_b.sql benchmark/analisar_pgbench.py; do
  [[ -s "$f" ]] || { echo "ERRO: falta $f"; exit 1; }
done
sha256sum "$DUMP" benchmark/bench_insert_a.sql benchmark/bench_insert_b.sql benchmark/analisar_pgbench.py "$0" > "$OUT/sha256.txt"
podman exec "$CONTAINER" pg_isready -U dba -d postgres
podman exec "$CONTAINER" mkdir -p /tmp/h3
for modelo in a b; do
  podman cp "benchmark/bench_insert_${modelo}.sql" "$CONTAINER:/tmp/h3/bench_insert_${modelo}.sql"
done
CSV="$OUT/resultados_insert.csv"
echo 'modelo,rodada,transacoes,tps,media_ms,mediana_ms,p95_ms,min_ms,max_ms,desvio_padrao_ms' > "$CSV"

sql_valor() {
  podman exec "$CONTAINER" psql -X -v ON_ERROR_STOP=1 -U dba -d "$DB" -Atc "$1"
}

restaurar() {
  echo "Restaurando somente $DB..."
  local sessoes tentativa
  for tentativa in $(seq 1 10); do
    sessoes=$(podman exec "$CONTAINER" psql -X -v ON_ERROR_STOP=1 -U dba -d postgres -Atc "SELECT count(*) FROM pg_stat_activity WHERE datname='$DB'")
    if [[ "$sessoes" == 0 ]]; then
      break
    fi
    echo "Banco ocupado ($sessoes conexao/oes). Tentativa $tentativa/10."
    sleep 2
  done
  [[ "$sessoes" == 0 ]] || { echo "ERRO: $sessoes sessoes persistentes"; exit 1; }
  podman exec "$CONTAINER" dropdb -U dba --if-exists "$DB"
  podman exec "$CONTAINER" createdb -U dba -T template0 "$DB"
  podman exec -i "$CONTAINER" pg_restore -U dba -d "$DB" --no-owner --no-privileges --exit-on-error --single-transaction < "$DUMP"
  local contagens
  contagens=$(sql_valor "SELECT (SELECT count(*) FROM parte_controle),(SELECT count(*) FROM parte),(SELECT count(*) FROM parte_historico),(SELECT count(*) FROM parte WHERE valid_at @> DATE '2026-09-01'),(SELECT count(*) FROM parte WHERE id_parte BETWEEN 200000 AND 279999),(SELECT count(*) FROM parte_controle WHERE id_parte BETWEEN 200000 AND 279999)")
  [[ "$contagens" == '100000|115182|84427|100000|0|0' ]] || { echo "ERRO: baseline incorreto: $contagens"; exit 1; }
  podman exec "$CONTAINER" psql -X -v ON_ERROR_STOP=1 -U dba -d "$DB" -c "CREATE SEQUENCE public.h3_insert_seq AS bigint START 200000 INCREMENT 1 MINVALUE 200000 MAXVALUE 279999 NO CYCLE CACHE 1;"
}

rodar() {
  local modelo=$1 rodada=$2 qt=$3 prefix=$4
  local script="/tmp/h3/bench_insert_${modelo,,}.sql"
  local resultado="$OUT/${prefix}.txt"
  local logs="$OUT/${prefix}_TRANSACOES.log"
  local esperado=$((N_CLIENTES * qt))
  echo "Executando $prefix; clientes=$N_CLIENTES threads=$N_THREADS transacoes/cliente=$qt"
  podman exec "$CONTAINER" sh -c "rm -f /tmp/h3/${prefix}.*"
  podman exec "$CONTAINER" pgbench -n -U dba -d "$DB" -c "$N_CLIENTES" -j "$N_THREADS" -t "$qt" -r -l --log-prefix="/tmp/h3/${prefix}" -f "$script" 2>&1 | tee "$resultado"
  podman exec "$CONTAINER" sh -c "cat /tmp/h3/${prefix}.*" > "$logs"
  local obtido
  obtido=$(wc -l < "$logs")
  [[ "$obtido" -eq "$esperado" ]] || { echo "ERRO: log $obtido de $esperado"; exit 1; }
  grep -Fq "number of transactions actually processed: $esperado/$esperado" "$resultado" || { echo 'ERRO: quantidade transacoes'; exit 1; }
  grep -Fq 'number of failed transactions: 0 (0.000%)' "$resultado" || { echo 'ERRO: falhas pgbench'; exit 1; }
  local resultado_validacao
  if [[ "$modelo" == A ]]; then
    resultado_validacao=$(sql_valor "SELECT (SELECT count(*) FROM parte_controle WHERE id_parte BETWEEN 200000 AND 279999),(SELECT count(*) FROM parte WHERE id_parte BETWEEN 200000 AND 279999),(SELECT count(*) FROM parte_historico)")
    [[ "$resultado_validacao" == "$esperado|0|84427" ]] || { echo "ERRO: validacao A: $resultado_validacao"; exit 1; }
  else
    resultado_validacao=$(sql_valor "SELECT (SELECT count(*) FROM parte WHERE id_parte BETWEEN 200000 AND 279999),(SELECT count(*) FROM parte WHERE id_parte BETWEEN 200000 AND 279999 AND valid_at = daterange(DATE '2026-09-01',NULL,'[)') AND NOT isempty(sys_period) AND lower(sys_period) IS NOT NULL AND upper_inf(sys_period) AND finalidade='benchmark_h3_insert' AND base_legal='teste_sintetico_h3'),(SELECT count(*) FROM parte_historico),(SELECT count(*) FROM parte_controle WHERE id_parte BETWEEN 200000 AND 279999)")
    [[ "$resultado_validacao" == "$esperado|$esperado|84427|0" ]] || { echo "ERRO: validacao B: $resultado_validacao"; exit 1; }
  fi
  printf 'modelo=%s\ntransacoes=%s\ncontagens=%s\n' "$modelo" "$esperado" "$resultado_validacao" > "$OUT/${prefix}_VALIDACAO.txt"
  if [[ "$rodada" != warmup ]]; then
    python3 benchmark/analisar_pgbench.py --log "$logs" --saida-pgbench "$resultado" --modelo "$modelo" --rodada "$rodada" >> "$CSV"
  fi
}

echo "Inicio: $(date -Iseconds)"
echo "Saida: $OUT"
echo "Rodadas: $N_RODADAS; transacoes por cliente: $N_TX; aquecimento: $N_AQUECIMENTO"
for modelo in A B; do
  restaurar
  rodar "$modelo" warmup "$N_AQUECIMENTO" "INSERT_${modelo}_WARMUP"
done
for rodada in $(seq 1 "$N_RODADAS"); do
  if (( rodada % 2 == 1 )); then ordem='A B'; else ordem='B A'; fi
  for modelo in $ordem; do
    restaurar
    rodar "$modelo" "$rodada" "$N_TX" "INSERT_${modelo}_R${rodada}"
  done
done
printf '\nRESULTADOS:\n'; cat "$CSV"
echo "Concluido em $(date -Iseconds); $OUT"
