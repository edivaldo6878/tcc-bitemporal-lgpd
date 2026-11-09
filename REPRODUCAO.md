# Reprodução dos experimentos

## Ambiente de referência

- Linux AlmaLinux 9 em WSL2.
- Podman.
- PostgreSQL 18.4.
- Python 3.
- pgbench.

O ambiente local utilizou um contêiner denominado
`tcc_postgres`.

## Dependências Python

Consultar `requirements.txt`.

## Escalas

H1 e H2 foram avaliadas funcionalmente nas escalas
de 10 mil e 100 mil partes sintéticas.

H3 utilizou a escala de 100 mil partes.

## Scripts

Gerador principal:

`gerar_dominio_v3.py`

Verificador:

`verificador_v3.py`

Modelo de domínio:

`db-dominio/`

Scripts de benchmark:

`benchmark/bench_select_a.sql`
`benchmark/bench_select_b.sql`
`benchmark/bench_update_a.sql`
`benchmark/bench_update_b.sql`
`benchmark/bench_insert_a.sql`
`benchmark/bench_insert_b.sql`

## Bancos utilizados

SELECT:
`tcc_dominio_100k`

UPDATE e INSERT:
`tcc_h3_update`

Os executores de UPDATE e INSERT utilizam um
backup de referência da base sintética de 100 mil
partes, com SHA-256:

`4bd94bfa565fc73f920f987349ba8b2539ce96faad72fdb77d246b740fd30e44`

## Advertência

Os scripts `executar_h3_update.sh` e
`executar_h3_insert.sh` possuem instruções
para eliminar, recriar e restaurar o banco
`tcc_h3_update`.

NÃO execute esses scripts em bancos com
dados que devam ser preservados.

O procedimento integral de reconstrução da
base e a execução independente dos testes
ainda dependem de validação.

## Limitações de interpretação

Os resultados representam o ambiente e as
condições experimentais documentadas.

Não foram realizados benchmarks repetidos de
latência para consultas históricas equivalentes
aos ensaios de consulta do estado corrente.

Os testes não utilizam dados pessoais reais.
