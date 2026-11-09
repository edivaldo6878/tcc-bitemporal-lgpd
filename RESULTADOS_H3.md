# Resultados experimentais H3 — PostgreSQL

## Objetivo

Documentar a comparação de vazão entre dois modelos
relacionais, na escala de 100 mil partes sintéticas:

- Modelo A: convencional.
- Modelo B: temporal.

## Resultados de TPS mediano

| Operação | Modelo A (TPS) | Modelo B (TPS) | Redução B |
|---|---:|---:|---:|
| SELECT | 30.307,90 | 26.026,73 | 14,13% |
| UPDATE | 3.115,30 | 2.668,54 | 14,34% |
| INSERT | 3.139,97 | 2.628,16 | 16,30% |

Cada operação possui cinco rodadas por modelo.

A mediana foi calculada separadamente para os cinco
valores de TPS de cada modelo e operação.

A redução percentual foi obtida por:

`100 * (TPS_A - TPS_B) / TPS_A`

## Arquivos de origem

- `evidencias/h3/select/resultados_select.csv`
- `evidencias/h3/update/lote_20261008_000101/resultados_update.csv`
- `evidencias/h3/insert/lote_20261008_005153/resultados_insert.csv`

## Interpretação

Os resultados indicam redução de vazão mediana do
modelo temporal no ambiente e nas condições examinadas.

O custo de armazenamento deve ser interpretado
separadamente, pois utiliza métricas diferentes.

As diferenças observadas não podem ser generalizadas
automaticamente para outros ambientes.

## Limitações

A escolha de privilegiar a mediana de TPS foi
explicitada retrospectivamente na monografia.

Não foram estabelecidos previamente limiares
quantitativos de aceitabilidade do desempenho.

Os testes utilizam dados sintéticos.
