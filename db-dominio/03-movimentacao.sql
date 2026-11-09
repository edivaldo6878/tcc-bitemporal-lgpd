-- 03: movimentacao_processual, tabela somente-insercao (contraponto: nem toda entidade
-- exige tratamento bitemporal; o proprio registro e' imutavel).
CREATE TABLE movimentacao_processual (
    id_movimentacao  bigint       GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_processo      integer      NOT NULL REFERENCES processo (id_processo),
    dt_movimentacao  timestamptz  NOT NULL DEFAULT clock_timestamp(),
    tp_movimentacao  varchar(40)  NOT NULL,
    descricao        text         NOT NULL,
    ds_agente        text         NOT NULL,       -- agente do ato, como texto (sintetico)
    agente           text         DEFAULT current_user,
    origem           text         DEFAULT current_setting('application_name')
);
COMMENT ON TABLE movimentacao_processual IS 'Somente insercao: UPDATE, DELETE e TRUNCATE sao bloqueados por trigger.';
CREATE INDEX ix_movimentacao_processo ON movimentacao_processual (id_processo, dt_movimentacao);

CREATE OR REPLACE FUNCTION fn_bloqueia_alteracao_movimentacao()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'movimentacao_processual e somente-insercao: % nao permitido', TG_OP
        USING ERRCODE = 'restrict_violation';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_movimentacao_somente_insercao
    BEFORE UPDATE OR DELETE ON movimentacao_processual
    FOR EACH ROW EXECUTE FUNCTION fn_bloqueia_alteracao_movimentacao();

CREATE TRIGGER trg_movimentacao_sem_truncate
    BEFORE TRUNCATE ON movimentacao_processual
    FOR EACH STATEMENT EXECUTE FUNCTION fn_bloqueia_alteracao_movimentacao();
