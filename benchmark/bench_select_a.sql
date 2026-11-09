\set id random(1, 100000)

SELECT id_parte, participacao
FROM parte_controle
WHERE id_parte = :id;
