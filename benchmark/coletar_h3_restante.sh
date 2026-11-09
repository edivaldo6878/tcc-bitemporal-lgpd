#!/usr/bin/env bash
set -Eeuo pipefail

cd "$HOME/tcc-bitemporal"

DB="tcc_h3_update"
DEST="evidencias/h3/consolidacao"
mkdir -p "$DEST"

DATA=$(date +%Y%m%d_%H%M%S)
LOG="$DEST/COLETA_H3_${DATA}.log"

exec > >(tee "$LOG") 2>&1

sql() {
    podman exec tcc_postgres \
        psql -X -v ON_ERROR_STOP=1 \
        -U dba -d "$DB" -c "$1"
}

echo "======================================="
echo " COLETA AUTOMATIZADA H3 - TCC UFABC"
echo "======================================="
date
echo "Banco: $DB"

echo
echo "ETAPA 1 - VALIDACAO"

VALIDACAO=$(podman exec tcc_postgres \
    psql -X -v ON_ERROR_STOP=1 \
    -U dba -d "$DB" -Atc "
SELECT
  CASE WHEN
    (SELECT count(*) FROM parte_controle) = 180000
    AND (SELECT count(*) FROM parte) = 115182
    AND (SELECT count(*) FROM parte_historico) = 84427
    AND (SELECT count(*) FROM parte_controle
         WHERE id_parte BETWEEN 200000 AND 279999) = 80000
  THEN 'OK'
  ELSE 'FALHA'
  END;")

if [[ "$VALIDACAO" != "OK" ]]; then
    echo "ERRO: volumetria inesperada."
    echo "Coleta interrompida sem alteracoes."
    exit 1
fi

echo "Volumetria validada: OK"

sql "
SELECT 'parte_controle' AS tabela, count(*) FROM parte_controle
UNION ALL
SELECT 'parte', count(*) FROM parte
UNION ALL
SELECT 'parte_historico', count(*) FROM parte_historico;
"

echo
echo "ETAPA 2 - ARMAZENAMENTO ATUAL"

sql "
SELECT
    relname AS tabela,
    pg_relation_size(oid) AS dados_bytes,
    pg_indexes_size(oid) AS indices_bytes,
    pg_total_relation_size(oid) AS total_bytes
FROM pg_class
WHERE oid IN (
    'public.parte'::regclass,
    'public.parte_controle'::regclass,
    'public.parte_historico'::regclass
)
ORDER BY relname;
"

echo
echo "ETAPA 3 - COMPARACAO DE ARMAZENAMENTO"
echo "Valores B provenientes dos passos 87 e 91."
echo "Valores A conferidos na base atual."

sql "
WITH medidas AS (
    SELECT
        'A'::text AS modelo,
        23085056::bigint AS antes_bytes,
        pg_total_relation_size(
            'public.parte_controle'::regclass
        ) AS depois_bytes
    UNION ALL
    SELECT
        'B',
        41328640::bigint,
        62439424::bigint
)
SELECT
    modelo,
    antes_bytes,
    depois_bytes,
    depois_bytes - antes_bytes AS crescimento_bytes,
    round(
        (depois_bytes - antes_bytes)::numeric
        / 80000, 2
    ) AS bytes_por_insercao
FROM medidas
ORDER BY modelo;
"

echo
echo "ETAPA 4 - CONSULTAS DE TEMPO VALIDO"

for DATA_VALIDO in \
    2022-06-01 \
    2023-06-01 \
    2024-06-01 \
    2025-06-01 \
    2026-09-01
do
    echo "----------------------------------"
    echo "Data valida: $DATA_VALIDO"

    sql "
EXPLAIN (ANALYZE, BUFFERS)
SELECT count(*)
FROM parte
WHERE id_parte < 200000
AND valid_at @> DATE '$DATA_VALIDO';
"
done

echo
echo "ETAPA 5 - CONSULTA BITEMPORAL HISTORICA"

sql "
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    id_parte, valid_at, sys_period, participacao
FROM parte_historico
WHERE id_parte = 72617
AND valid_at @> DATE '2025-06-01'
AND sys_period @>
    TIMESTAMPTZ '2026-10-03 21:25:32.192434+00';
"

echo
echo "ETAPA 6 - AMOSTRA DE VERSOES HISTORICAS"

sql "
WITH amostra AS (
    SELECT
        hist_id,
        id_parte,
        valid_at,
        lower(sys_period) AS inicio_tx,
        upper(sys_period) AS fim_tx,
        upper(sys_period) - lower(sys_period)
            AS duracao_tx
    FROM parte_historico
    WHERE NOT upper_inf(sys_period)
    ORDER BY hist_id
    LIMIT 20
)
SELECT * FROM amostra ORDER BY hist_id;
"

echo
echo "ETAPA 7 - REFERENCIAS DAS EVIDENCIAS"

for ARQ in \
    evidencias/h3/armazenamento/BASELINE_RESTAURADA.txt \
    evidencias/h3/armazenamento/ARMAZENAMENTO_POS_INSERT_B.txt \
    evidencias/h3/armazenamento/ARMAZENAMENTO_POS_INSERT_A.txt \
    evidencias/h3/armazenamento/VOLUMETRIA_POS_INSERT_B.txt \
    evidencias/h3/historico/EXPLAIN_BITEMPORAL_10_EXECUCOES.txt
do
    if [[ -f "$ARQ" ]]; then
        sha256sum "$ARQ"
    else
        echo "EVIDENCIA AUSENTE: $ARQ"
    fi
done

echo
echo "======================================="
echo " COLETA CONCLUIDA"
echo "======================================="
date
echo "Relatorio: $LOG"
