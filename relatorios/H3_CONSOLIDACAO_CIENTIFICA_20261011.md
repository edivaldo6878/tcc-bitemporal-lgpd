# H3 — Consolidação de desempenho e armazenamento

## Protocolo e delimitação

Comparação dos Modelos A (convencional) e B (temporal), na escala de 100 mil partes, com cinco rodadas oficiais por modelo e operação.

## Resultados de throughput

| Operação | Média A | Média B | Mediana A | Mediana B | CV A | CV B | Redução média | Redução mediana |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| SELECT | 28917.93 | 26697.37 | 30307.90 | 26026.73 | 8.37% | 6.64% | 7.68% | 14.13% |
| UPDATE | 3136.28 | 2613.96 | 3115.30 | 2668.54 | 1.63% | 5.37% | 16.65% | 14.34% |
| INSERT | 3113.43 | 2558.74 | 3139.97 | 2628.16 | 1.44% | 8.79% | 17.82% | 16.30% |

## Interpretação

Em UPDATE e INSERT, o Modelo B apresentou throughput inferior ao Modelo A nas cinco rodadas oficiais, com faixas observadas sem sobreposição. Para SELECT, as faixas se sobrepõem e o Modelo B superou A em duas rodadas. Portanto, o custo de leitura deve ser interpretado de forma mais cautelosa.

## Armazenamento

| Medida | Modelo A | Modelo B |
|---|---:|---:|
| Estoque estático na base original (bytes) | 25.878.528 | 88.727.552 |
| Incremento após 80 mil INSERTs (bytes) | 9.969.664 | 21.110.784 |
| Incremento por inserção (bytes) | 124,62 | 263,88 |

A razão estática B/A é aproximadamente 3,43. A razão incremental após INSERT é aproximadamente 2,12.

## Limitações

- O benchmark comparativo foi realizado somente na escala de 100 mil partes.
- Não houve medição específica de armazenamento após UPDATE.
- A comparação incremental não incorpora todo o histórico preexistente.
- A base original e a base restaurada possuem tamanhos físicos distintos.
- Não foi executado benchmark de desempenho na escala de 1 milhão.
- As diferenças observadas não constituem, isoladamente, evidência de significância estatística.

## Proveniência

- CSV oficial de SELECT: evidencias/h3/select/resultados_select.csv
- CSV oficial de UPDATE: lote_20261008_000101
- CSV oficial de INSERT: lote_20261008_005153
- Evidências de armazenamento: evidencias/h3/armazenamento/
- Commit das medições de armazenamento: d8b1aad
