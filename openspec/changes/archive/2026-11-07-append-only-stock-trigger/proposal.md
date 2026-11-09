# Proposal: Append-Only Stock Trigger

## Why
La regla de negocio RN-12 y los ejercicios 2 y 7 del parcial exigen que la tabla `movimiento_stock` sea estrictamente de sólo agregado: nadie puede modificar ni borrar sus filas, venga de donde venga la operación. La comparación automática de Alembic (`--autogenerate`) no detecta funciones ni disparadores, por lo que debe escribirse una migración manual dedicada que cree la función PL/pgSQL y el trigger en PostgreSQL, acompañada del caso de prueba C-14.

## What Changes
- Migración manual Alembic en `parcial/migrations/versions/0003_trigger_solo_agregado.py`:
  - Creación de la función `fn_proteger_movimiento_stock_solo_agregado()` en PL/pgSQL que lanza excepción fatal si `TG_OP` es `UPDATE` o `DELETE`.
  - Creación del disparador `tr_movimiento_stock_solo_agregado` que intercepta `BEFORE UPDATE OR DELETE ON movimiento_stock FOR EACH ROW`.
  - Función `downgrade()` limpia que elimina el trigger y la función.
  - Comentario explicativo obligatorio indicando por qué se escribió a mano.
- Script SQL de verificación para el Caso C-14 en `parcial/test/solo_agregado.sql`:
  - Inserción de un registro válido en `movimiento_stock`.
  - Intento de ejecución de `UPDATE` sobre el registro (rechazado por el trigger).
  - Intento de ejecución de `DELETE` sobre el registro (rechazado por el trigger).
  - Consulta `SELECT` final que demuestra que el registro original permanece inalterado.
- Tests unitarios en `parcial/test/test_trigger.py` para verificar el comportamiento y la definición del trigger.

## Capabilities

### Modified Capabilities
- `data-persistence`: Incorporación del disparador de base de datos para la inmutabilidad estricta (sólo agregado) de `movimiento_stock`.

## Impact
- Bloquea cualquier modificación o borrado de filas en `movimiento_stock` a nivel de motor de base de datos.
- Provee la base para el caso de prueba C-14 y la evidencia obligatoria requerida para la entrega.
