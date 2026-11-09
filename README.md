# Arquitetura temporal de governança de dados pessoais

## Sobre o projeto

Repositório de apoio ao Trabalho de Conclusão de Curso
de Especialização em Tecnologias e Sistemas de Informação
da Universidade Federal do ABC (UFABC), 2026.

**Autor:** Edivaldo Vicente dos Santos

**Orientador:** Prof. Dr. Danilo Trabuco do Amaral

**Título:** Arquitetura temporal de governança de dados
pessoais em SGBD relacional: rastreabilidade, auditoria
e qualidade de dados para apoio à conformidade com a LGPD.

## Objetivo

Investigar uma arquitetura de governança de dados pessoais
com modelagem bitemporal em PostgreSQL, contemplando
tempo válido e tempo de transação, registros de auditoria
e mecanismos de rastreabilidade.

## Modelos avaliados

- Modelo A: modelo relacional convencional de referência.
- Modelo B: modelo com representação temporal e histórico.

## Hipóteses

- H1: correção funcional da implementação temporal.
- H2: rastreabilidade e capacidade de auditoria.
- H3: custo técnico da camada temporal, medido por
  armazenamento, vazão e latência.

A avaliação funcional utilizou bases sintéticas de
10 mil e 100 mil partes.

Os ensaios comparativos de desempenho H3 foram
realizados na escala de 100 mil partes.

## Organização

- `db-dominio/`: esquema relacional do domínio.
- `db-init/`: scripts de inicialização e evolução.
- `benchmark/`: consultas e executores de desempenho.
- `evidencias/`: registros de testes e medições.
- `relatorios/`: análises e consolidações.
- `gerar_dominio_v3.py`: gerador sintético.
- `verificador_v3.py`: verificador funcional.
- `REPRODUCAO.md`: orientações de reprodução.
- `MANIFESTO_EVIDENCIAS.md`: evidências selecionadas.

## Limitações

Os experimentos utilizaram dados sintéticos.

A avaliação não representa garantia automática de
conformidade com a LGPD.

Consultas históricas foram avaliadas funcionalmente,
mas não por benchmark repetido equivalente às
consultas do estado atual.

Os executores de INSERT e UPDATE podem recriar
o banco de testes. Consulte `REPRODUCAO.md`
antes de qualquer execução.

## Estado da publicação

Este repositório reúne artefatos de pesquisa
e evidências selecionadas. A reprodução integral
em ambiente externo ainda não foi certificada.
