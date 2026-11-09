# Limitações técnicas identificadas

## 1. Cobertura do teste TC-V3-10

Arquivo:
`verificador_v3.py`

O TC-V3-10 percorre as versões encerradas presentes
no conjunto de versões observadas de cada parte.

Para cada versão encerrada, verifica se existe
ao menos uma versão da mesma parte cujo início
de tempo de transação corresponda ao término
da versão examinada.

O teste não exige que a sucessora pertença ao
mesmo segmento de tempo válido (`valid_at`).

Também não verifica isoladamente a unicidade
da sucessora.

Assim, o resultado do TC-V3-10 não deve ser
interpretado como demonstração exaustiva
da continuidade de todas as cadeias bitemporais.

Esta observação decorre da inspeção estática
do código e não altera os resultados dos
testes experimentais registrados.

## 2. Condição de atualização da anonimização

Arquivo:
`db-dominio/05-anonimizacao.sql`

A função `anonimizar_parte()` utiliza a condição:

`nome <> v_marcador`

tanto nas versões correntes quanto nas históricas.

Uma versão cujo nome já corresponda ao marcador
não será atualizada pela função, mesmo que
outros atributos pessoais ainda contenham valores.

Trata-se de um caso-limite identificado pela
análise estática da condição SQL.

Não foi demonstrado, nos resultados experimentais
disponíveis, que essa situação tenha ocorrido.

## 3. Registro da anonimização

A função insere um registro em
`anonimizacao_log` a cada chamada concluída,
inclusive quando nenhuma versão é atualizada.

O comportamento merece avaliação específica
quanto à repetição da operação e à interpretação
dos registros de auditoria.

## 4. Preservação da evidência

Os arquivos originais foram mantidos sem
alterações para preservar a correspondência
entre implementação, testes e resultados
relatados na monografia.

Qualquer alteração futura deverá ser
versionada e acompanhada de novos testes,
quando pertinente.
