-- 04: Modelo A (controle). Mesma estrutura logica de negocio de parte, apenas o estado
-- corrente, sem periodos temporais, historico ou metadados de versao.
CREATE TABLE parte_controle (
    id_parte       integer      PRIMARY KEY,
    id_processo    integer      NOT NULL REFERENCES processo (id_processo),
    tp_pessoa      char(1)      NOT NULL CHECK (tp_pessoa IN ('F', 'J')),
    participacao   char(1)      NOT NULL CHECK (participacao IN ('A', 'P', 'T', 'F')),
    nome           text         NOT NULL,
    nome_social    text,
    tp_documento   varchar(4)   NOT NULL,
    nr_documento   text         NOT NULL,
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
    CHECK ((tp_pessoa = 'F' AND tp_documento = 'CPF') OR (tp_pessoa = 'J' AND tp_documento = 'CNPJ'))
);
COMMENT ON TABLE parte_controle IS 'Modelo A: baseline sem mecanismo temporal, para a comparacao de desempenho.';
CREATE INDEX ix_parte_controle_processo ON parte_controle (id_processo);
