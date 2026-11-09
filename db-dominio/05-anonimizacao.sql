-- 05: anonimizacao controlada de uma parte, com evidencia minima registrada.
-- Remove os dados pessoais de TODAS as versoes (corrente e historico) e preserva
-- identificadores, periodos, operacao e metadados. Restaura o contexto do chamador.
CREATE TABLE anonimizacao_log (
    anon_id            bigserial    PRIMARY KEY,
    id_parte           integer      NOT NULL,
    executado_em       timestamptz  NOT NULL DEFAULT clock_timestamp(),
    executado_por      text         NOT NULL DEFAULT current_user,
    fundamento         text         NOT NULL CHECK (btrim(fundamento) <> ''),
    versoes_historico  integer      NOT NULL,
    versoes_correntes  integer      NOT NULL
);
COMMENT ON TABLE anonimizacao_log IS 'Evidencia minima: qual parte, quando, por quem e com qual fundamento.';

CREATE OR REPLACE FUNCTION anonimizar_parte(p_id_parte integer, p_fundamento text)
RETURNS integer AS $$
DECLARE
    v_marcador constant text := '[DADO PESSOAL REMOVIDO]';
    v_fin_ant  text := coalesce(current_setting('tcc.finalidade', true), '');
    v_base_ant text := coalesce(current_setting('tcc.base_legal', true), '');
    n_corr integer;
    n_hist integer;
BEGIN
    IF p_fundamento IS NULL OR btrim(p_fundamento) = '' THEN
        RAISE EXCEPTION 'anonimizar_parte: fundamento obrigatorio';
    END IF;

    PERFORM set_config('tcc.finalidade', 'anonimizacao', true);
    PERFORM set_config('tcc.base_legal', p_fundamento, true);

    -- 1o a(s) linha(s) corrente(s): o UPDATE arquiva a versao ainda em claro no historico.
    UPDATE parte
       SET nome = v_marcador, nr_documento = v_marcador, nome_social = NULL,
           dt_nascimento = NULL, email = NULL, telefone = NULL, logradouro = NULL,
           numero = NULL, complemento = NULL, bairro = NULL, cidade = NULL,
           uf = NULL, cep = NULL
     WHERE id_parte = p_id_parte AND nome <> v_marcador;
    GET DIAGNOSTICS n_corr = ROW_COUNT;

    -- 2o TODO o historico da parte, incluindo a copia que acabou de ser arquivada.
    UPDATE parte_historico
       SET nome = v_marcador, nr_documento = v_marcador, nome_social = NULL,
           dt_nascimento = NULL, email = NULL, telefone = NULL, logradouro = NULL,
           numero = NULL, complemento = NULL, bairro = NULL, cidade = NULL,
           uf = NULL, cep = NULL
     WHERE id_parte = p_id_parte AND nome <> v_marcador;
    GET DIAGNOSTICS n_hist = ROW_COUNT;

    INSERT INTO anonimizacao_log (id_parte, fundamento, versoes_historico, versoes_correntes)
    VALUES (p_id_parte, p_fundamento, n_hist, n_corr);

    PERFORM set_config('tcc.finalidade', v_fin_ant, true);
    PERFORM set_config('tcc.base_legal', v_base_ant, true);

    RETURN n_corr + n_hist;
END;
$$ LANGUAGE plpgsql;
