BEGIN;

SELECT set_config('tcc.finalidade', 'benchmark_h3_insert', true);
SELECT set_config('tcc.base_legal', 'teste_sintetico_h3', true);

INSERT INTO parte_controle (
    id_parte,
    id_processo,
    tp_pessoa,
    participacao,
    nome,
    tp_documento,
    nr_documento
)
VALUES (
    nextval('public.h3_insert_seq'),
    1,
    'F',
    'A',
    'TESTE SINTETICO H3 INSERT',
    'CPF',
    '00000000000'
);

COMMIT;
