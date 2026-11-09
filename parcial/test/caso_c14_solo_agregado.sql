-- ============================================================================
-- CASO DE PRUEBA C-14: Regla RN-12 (movimiento_stock es de sólo agregado)
-- ============================================================================
-- Consigna: UPDATE y DELETE sobre movimiento_stock en psql
-- Resultado esperado: Los dos, rechazados por el disparador
-- ============================================================================
-- Ejecutar en psql después de correr: python seed.py
-- Comando sugerido: psql -U postgres -d libreria -f test/caso_c14_solo_agregado.sql
-- ============================================================================

\echo '--- 1. Insertando un movimiento de prueba válido ---'
INSERT INTO movimiento_stock (libro_id, usuario_id, cantidad, motivo, cuando)
VALUES (1, 1, 5, 'Ingreso extraordinario de prueba C-14', NOW())
RETURNING id, libro_id, usuario_id, cantidad, motivo, cuando;

\echo '--- 2. Intentando UPDATE sobre movimiento_stock (debe ser rechazado por el trigger) ---'
-- Resultado esperado: ERROR: La tabla movimiento_stock es de solo agregado: no se permite UPDATE
UPDATE movimiento_stock
SET cantidad = 10
WHERE motivo = 'Ingreso extraordinario de prueba C-14';

\echo '--- 3. Intentando DELETE sobre movimiento_stock (debe ser rechazado por el trigger) ---'
-- Resultado esperado: ERROR: La tabla movimiento_stock es de solo agregado: no se permite DELETE
DELETE FROM movimiento_stock
WHERE motivo = 'Ingreso extraordinario de prueba C-14';

\echo '--- 4. Verificando que el registro sigue existiendo inalterado ---'
-- Resultado esperado: La fila original con cantidad = 5 sigue intacta
SELECT id, libro_id, usuario_id, cantidad, motivo, cuando
FROM movimiento_stock
WHERE motivo = 'Ingreso extraordinario de prueba C-14';
