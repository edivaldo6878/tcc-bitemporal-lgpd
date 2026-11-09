-- 02: trigger auxiliar de tempo de transacao para parte.
-- O instante e' lido uma unica vez (versoes contiguas, sem lacuna) e GREATEST garante
-- intervalo nao vazio e ordenado mesmo se o relogio do sistema recuar.
CREATE OR REPLACE FUNCTION fn_versiona_parte()
RETURNS TRIGGER AS $$
DECLARE
    t_corte timestamptz;
BEGIN
    t_corte := GREATEST(clock_timestamp(),
                        lower(OLD.sys_period) + interval '1 microsecond');

    INSERT INTO parte_historico
        (id_parte, id_processo, tp_pessoa, participacao, nome, nome_social,
         tp_documento, nr_documento, dt_nascimento, email, telefone,
         logradouro, numero, complemento, bairro, cidade, uf, cep,
         valid_at, sys_period, agente, origem, txid, finalidade, base_legal,
         operacao, encerrado_por)
    VALUES
        (OLD.id_parte, OLD.id_processo, OLD.tp_pessoa, OLD.participacao, OLD.nome, OLD.nome_social,
         OLD.tp_documento, OLD.nr_documento, OLD.dt_nascimento, OLD.email, OLD.telefone,
         OLD.logradouro, OLD.numero, OLD.complemento, OLD.bairro, OLD.cidade, OLD.uf, OLD.cep,
         OLD.valid_at, tstzrange(lower(OLD.sys_period), t_corte),
         OLD.agente, OLD.origem, OLD.txid, OLD.finalidade, OLD.base_legal,
         CASE WHEN TG_OP = 'DELETE' THEN 'D' ELSE 'U' END, current_user);

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;

    NEW.sys_period := tstzrange(t_corte, NULL);
    NEW.agente     := current_user;
    NEW.origem     := current_setting('application_name');
    NEW.txid       := txid_current();
    NEW.finalidade := nullif(current_setting('tcc.finalidade', true), '');
    NEW.base_legal := nullif(current_setting('tcc.base_legal', true), '');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_versiona_parte
    BEFORE UPDATE OR DELETE ON parte
    FOR EACH ROW EXECUTE FUNCTION fn_versiona_parte();
