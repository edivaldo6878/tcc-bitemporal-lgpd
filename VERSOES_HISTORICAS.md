# Versões históricas e evolução do protótipo

## Finalidade

Este documento distingue os artefatos utilizados
na avaliação final dos materiais produzidos em
etapas anteriores do desenvolvimento.

## Implementação final avaliada

Os principais arquivos associados à versão V3 são:

- `gerar_dominio_v3.py`
- `verificador_v3.py`
- `db-dominio/01-processo-parte.sql`
- `db-dominio/02-trigger-versionamento.sql`
- `db-dominio/03-movimentacao.sql`
- `db-dominio/04-modelo-a.sql`
- `db-dominio/05-anonimizacao.sql`

As evidências funcionais estão registradas em:

- `evidencias/TC_V3_10K_POS_FIX_20261003_1842.txt`
- `evidencias/TC_V3_100K_POS_FIX_20261003_1842.txt`

Os resultados de desempenho estão identificados
em `MANIFESTO_EVIDENCIAS.md`.

## Artefatos de etapas anteriores

Os seguintes arquivos pertencem a etapas
anteriores ou atividades auxiliares:

- `gerar_dados_v2.py`
- `verificador_h1.py`
- `verificador_v2.py`
- `db-init/`
- `scripts/tc_h2_governanca.sql`

Esses arquivos são preservados como registros
da evolução do protótipo e não devem ser
tratados automaticamente como o procedimento
oficial da avaliação final.

A documentação desses componentes não constitui
uma nova execução ou validação experimental.

## Limitações

A existência de diferentes versões não significa
que todas foram avaliadas com os mesmos critérios.

Para interpretar os resultados científicos,
utilize prioritariamente a implementação V3 e
os registros oficiais indicados no manifesto.
