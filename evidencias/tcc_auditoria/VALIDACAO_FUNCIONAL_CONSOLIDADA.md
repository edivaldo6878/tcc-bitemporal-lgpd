# Validação funcional consolidada — TCC UFABC

Gerado em: 2026-10-08T04:33:58

## Evidências examinadas

### V3 — 100 mil partes

Arquivo: `evidencias/TC_V3_100K_POS_FIX_20261003_1842.txt`
SHA-256: `4af56ef2fbad42ae5d39cd9c9a6c465975792a8c23735df884d295c5267cda1b`

```text
Banco: tcc_dominio_100k
Partes no gabarito: 100000
TC-V3-01 APROVADO   Quantidade de processos igual ao gabarito  (0 falhas)
TC-V3-02 APROVADO   Quantidade de movimentacoes igual ao gabarito  (0 falhas)
TC-V3-03 APROVADO   Ausencia de sobreposicao bitemporal  (0 falhas)
TC-V3-04 APROVADO   Numero de versoes por parte  (0 falhas)
TC-V3-05 APROVADO   Conteudo pessoal de cada versao  (0 falhas)
TC-V3-06 APROVADO   Dados nao pessoais preservados  (0 falhas)
TC-V3-07 APROVADO   Tempo valido correto  (0 falhas)
TC-V3-08 APROVADO   Inicio do tempo de transacao correto  (0 falhas)
TC-V3-09 APROVADO   Metadados de governanca presentes  (0 falhas)
TC-V3-10 APROVADO   Contiguidade do tempo de transacao  (0 falhas)
TC-V3-11 APROVADO   Anonimizacao registrada e fundamentada  (0 falhas)
TC-V3-12 APROVADO   Modelo A consistente com o estado corrente  (0 falhas)
RESULTADO GERAL: APROVADO
```

### V3 — 10 mil partes

Arquivo: `evidencias/TC_V3_10K_POS_FIX_20261003_1842.txt`
SHA-256: `1694a84fe1fb045af2c8f266599ce4f56971415ff1636c8f299260de9b254a06`

```text
Banco: tcc_dominio
Partes no gabarito: 10000
TC-V3-01 APROVADO   Quantidade de processos igual ao gabarito  (0 falhas)
TC-V3-02 APROVADO   Quantidade de movimentacoes igual ao gabarito  (0 falhas)
TC-V3-03 APROVADO   Ausencia de sobreposicao bitemporal  (0 falhas)
TC-V3-04 APROVADO   Numero de versoes por parte  (0 falhas)
TC-V3-05 APROVADO   Conteudo pessoal de cada versao  (0 falhas)
TC-V3-06 APROVADO   Dados nao pessoais preservados  (0 falhas)
TC-V3-07 APROVADO   Tempo valido correto  (0 falhas)
TC-V3-08 APROVADO   Inicio do tempo de transacao correto  (0 falhas)
TC-V3-09 APROVADO   Metadados de governanca presentes  (0 falhas)
TC-V3-10 APROVADO   Contiguidade do tempo de transacao  (0 falhas)
TC-V3-11 APROVADO   Anonimizacao registrada e fundamentada  (0 falhas)
TC-V3-12 APROVADO   Modelo A consistente com o estado corrente  (0 falhas)
RESULTADO GERAL: APROVADO
```

### Consistência e concorrência

Arquivo: `evidencias/TC_C_E_DOMINIO_20261003_1814.txt`
SHA-256: `ec0f9f7033058416c7ff65b75179a59c8d7b97ac87a8ac0653496873d0d87819`

```text
TC-C-01  APROVADO   Insercao sobreposta no mesmo id_parte e rejeitada
TC-C-02  APROVADO   Insercao que sobrepoe dois periodos e rejeitada
TC-C-03  APROVADO   UPDATE que cria sobreposicao e rejeitado
TC-C-04  APROVADO   Tentativas rejeitadas nao deixam historico parcial
TC-C-05  APROVADO   Periodos adjacentes sao aceitos
TC-C-06  APROVADO   Mesmo periodo em outra entidade e aceito
TC-E-01  APROVADO   READ COMMITTED serializa os UPDATEs sem perda de versao
TC-E-02  APROVADO   REPEATABLE READ detecta conflito e rollback nao deixa versao parcial
TC-E-03  APROVADO   Insercoes concorrentes respeitam commit e rollback
TC-E-04  APROVADO   8 sessoes x 150 UPDATEs sem perda de versoes
RESULTADO GERAL: APROVADO
```

## Conclusão

A avaliação funcional foi consolidada a partir dos
relatórios de execução disponíveis.

A aprovação dos verificadores evidencia atendimento
aos critérios automatizados examinados, mas não
equivale à certificação integral de conformidade LGPD.
