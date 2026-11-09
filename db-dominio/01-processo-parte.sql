-- Modelo de dominio generico (3 tabelas), inspirado conceitualmente na estrutura de
-- sistemas de processo judicial e administrativo (PJe e SEI), sem reproduzir
-- scripts, nomes internos nem dados. Todos os dados sao sinteticos.
--
-- 01: extensao, processo (sem tratamento temporal) e parte (bitemporal).
CREATE EXTENSION IF NOT EXISTS btree_gist;

CREATE TABLE processo (
    id_processo        integer      PRIMARY KEY,
    nr_processo        varchar(25)  NOT NULL UNIQUE,   -- formato CNJ, sintetico por construcao
    classe             varchar(60)  NOT NULL,
    orgao_julgador     varchar(80)  NOT NULL,
    dt_autuacao        date         NOT NULL,
    situacao           char(1)      NOT NULL CHECK (situacao IN ('A', 'S', 'B')),  -- ativo, suspenso, baixado
    in_segredo_justica boolean      NOT NULL DEFAULT false
);
COMMENT ON TABLE processo IS 'Contexto do processo. Sem tratamento temporal: estavel para os fins da POC.';

-- parte: pessoa vinculada ao processo (pessoa e vinculo simplificados em uma tabela).
-- Tempo valido: valid_at com WITHOUT OVERLAPS (nativo, PostgreSQL 18).
-- Tempo de transacao: sys_period, mantido pelo trigger de versionamento (arquivo 02).
CREATE TABLE parte (
    id_parte       integer      NOT NULL,
    id_processo    integer      NOT NULL REFERENCES processo (id_processo),
    tp_pessoa      char(1)      NOT NULL CHECK (tp_pessoa IN ('F', 'J')),
    participacao   char(1)      NOT NULL CHECK (participacao IN ('A', 'P', 'T', 'F')),  -- ativo, passivo, terceiro, fiscal
    nome           text         NOT NULL,
    nome_social    text,
    tp_documento   varchar(4)   NOT NULL,
    nr_documento   text         NOT NULL,        -- sintetico, com digitos verificadores invalidos
    dt_nascimento  date,
    email          text,
    telefone       text,
    logradouro     text,
    numero         text,
    complemento    text,
    bairro         text,
    cidade         text,
    uf             char(2),
    cep            text,
    valid_at       daterange    NOT NULL,
    sys_period     tstzrange    NOT NULL DEFAULT tstzrange(clock_timestamp(), NULL),
    -- metadados de governanca por versao (H2)
    agente         text         DEFAULT current_user,
    origem         text         DEFAULT current_setting('application_name'),
    txid           bigint       DEFAULT txid_current(),
    finalidade     text         DEFAULT nullif(current_setting('tcc.finalidade', true), ''),
    base_legal     text         DEFAULT nullif(current_setting('tcc.base_legal', true), ''),
    PRIMARY KEY (id_parte, valid_at WITHOUT OVERLAPS),
    CHECK ((tp_pessoa = 'F' AND tp_documento = 'CPF') OR (tp_pessoa = 'J' AND tp_documento = 'CNPJ'))
);
COMMENT ON TABLE parte IS 'Versao vigente de cada fato (bitemporal). Versoes substituidas vao para parte_historico.';
CREATE INDEX ix_parte_processo ON parte (id_processo);

-- Historico: mesmas colunas de parte, alimentado exclusivamente pelo trigger.
CREATE TABLE parte_historico (
    hist_id        bigserial    PRIMARY KEY,
    LIKE parte,
    operacao       char(1)      NOT NULL CHECK (operacao IN ('U', 'D')),
    encerrado_por  text,
    arquivado_em   timestamptz  NOT NULL DEFAULT clock_timestamp()
);
COMMENT ON TABLE parte_historico IS 'Versoes substituidas ou removidas de parte, com o tempo de transacao fechado.';
CREATE INDEX ix_parte_hist_tempo ON parte_historico USING gist (id_parte, sys_period);
