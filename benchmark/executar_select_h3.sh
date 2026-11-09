#!/bin/bash
set -euo pipefail

DB="tcc_dominio_100k"
CONT="tcc_postgres"
DIR_HOST="evidencias/h3/select"
DIR_CONT="/tmp/h3"

mkdir -p "$DIR_HOST"

CSV="$DIR_HOST/resultados_select.csv"

echo \
"modelo,rodada,transacoes,tps,media_ms,mediana_ms,p95_ms,min_ms,max_ms,desvio_padrao_ms" \
> "$CSV"


executar()
{
    MODELO="$1"
    RODADA="$2"

    if [ "$MODELO" = "A" ]; then
        SCRIPT="bench_select_a.sql"
    else
        SCRIPT="bench_select_b.sql"
    fi

    PREFIX="select_${MODELO}_r${RODADA}"
    OUT="$DIR_HOST/SELECT_${MODELO}_R${RODADA}.txt"
    LOG="$DIR_HOST/SELECT_${MODELO}_R${RODADA}_TRANSACOES.log"

    echo
    echo "======================================================"
    echo "SELECT MODELO $MODELO - RODADA $RODADA"
    echo "======================================================"

    podman exec "$CONT" sh -lc "
        rm -f ${DIR_CONT}/${PREFIX}.*
        cd ${DIR_CONT}

        pgbench \
          -n \
          -U dba \
          -d ${DB} \
          -c 8 \
          -j 4 \
          -t 10000 \
          -r \
          -l \
          --log-prefix=${PREFIX} \
          -f ${SCRIPT}
    " | tee "$OUT"

    podman exec "$CONT" sh -lc \
        "cat ${DIR_CONT}/${PREFIX}.*" \
        > "$LOG"

    LINHAS=$(wc -l < "$LOG")

    if [ "$LINHAS" -ne 80000 ]; then
        echo "ERRO: esperado 80000 registros; obtido $LINHAS"
        exit 1
    fi

    python3 benchmark/analisar_pgbench.py \
        --log "$LOG" \
        --saida-pgbench "$OUT" \
        --modelo "$MODELO" \
        --rodada "$RODADA" \
        >> "$CSV"
}


for R in 1 2 3 4 5
do
    executar A "$R"
    executar B "$R"
done

echo
echo "======================================================"
echo "SELECT H3 CONCLUIDO"
echo "======================================================"
cat "$CSV"
