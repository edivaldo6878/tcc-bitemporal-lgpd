\set id random(1000, 100999)

BEGIN;

SELECT set_config('tcc.finalidade', 'benchmark_h3_update', true);
SELECT set_config('tcc.base_legal', 'teste_sintetico_h3', true);

UPDATE parte
SET participacao =
    CASE
        WHEN participacao = 'A' THEN 'P'
        ELSE 'A'
    END
WHERE id_parte = :id
  AND valid_at @> DATE '2026-09-01';

COMMIT;
