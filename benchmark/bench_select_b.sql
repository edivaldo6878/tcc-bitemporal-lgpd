\set id random(1, 100000)

SELECT id_parte, participacao
FROM parte
WHERE id_parte = :id
  AND valid_at @> DATE '2026-09-01';
