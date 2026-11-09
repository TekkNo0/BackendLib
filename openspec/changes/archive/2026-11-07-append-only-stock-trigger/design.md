# Design: Append-Only Stock Trigger

## Context
El parcial establece en la regla de negocio RN-12 que `movimiento_stock` es de sólo agregado: nadie puede modificar ni borrar sus filas. En el Ejercicio 2 y 7 se detalla que este mecanismo se garantiza mediante un disparador (trigger) en PostgreSQL instalado por una migración escrita a mano, dado que `--autogenerate` de Alembic no detecta funciones ni triggers.

## Goals / Non-Goals

**Goals:**
- Implementar la función PL/pgSQL `fn_proteger_movimiento_stock_solo_agregado()` que lanza una excepción ante cualquier intento de UPDATE o DELETE.
- Asociar el trigger `tr_movimiento_stock_solo_agregado` ejecutado `BEFORE UPDATE OR DELETE ON movimiento_stock FOR EACH ROW`.
- Incluir en la migración un comentario de revisión técnica que explique por qué se escribió a mano.
- Proveer el script `test/solo_agregado.sql` que demuestra el caso de prueba C-14 para la corrección y la carpeta de evidencia.

**Non-Goals:**
- Implementar servicios o routers de ventas o reposición — asignados a C-06 y C-07.
- Modificar el modelo Python `MovimientoStock` (ya modelado en C-02).

## Decisions

### D1: Función PL/pgSQL y Disparador BEFORE
- **Decisión**: La función en PostgreSQL comprueba `IF TG_OP IN ('UPDATE', 'DELETE') THEN RAISE EXCEPTION 'movimiento_stock es de sólo agregado: no se permite %', TG_OP; END IF;`. El trigger se crea como `BEFORE UPDATE OR DELETE ON movimiento_stock FOR EACH ROW EXECUTE FUNCTION fn_proteger_movimiento_stock_solo_agregado();`.
- **Razón**: Interceptar en el nivel `BEFORE` detiene la operación antes de realizar cualquier cambio en los bloques de datos y aborta inmediatamente la transacción.
- **Alternativas consideradas**:
  - *Trigger INSTEAD OF*: Solo aplica a vistas en PostgreSQL, no a tablas base.
  - *Control a nivel de rol de base de datos*: Mencionado en la sección 6.9 como mecanismo secundario de defensa en profundidad, pero la consigna exige explícitamente el disparador en la base instalado por migración.

### D2: Migración Manual con Reversibilidad Total (`downgrade`)
- **Decisión**: En `upgrade()`, `op.execute(...)` crea la función y el trigger. En `downgrade()`, `op.execute("DROP TRIGGER IF EXISTS ...; DROP FUNCTION IF EXISTS ...;")`.
- **Razón**: Garantiza que `alembic downgrade base` y `upgrade head` funcionen de forma 100% reversible (requisito de Ejercicio 2).

### D3: Script de Prueba C-14 (`test/solo_agregado.sql`)
- **Decisión**: Crear `test/solo_agregado.sql` estructurado en 4 pasos: insert inicial, update fallido, delete fallido y select comprobatorio.
- **Razón**: Requisito explícito de la consigna para el Caso C-14 y el entregable en la carpeta `evidencia/`.

## Risks / Trade-offs

- **[Riesgo: Migraciones ejecutadas en motores distintos a PostgreSQL]** → *Mitigación*: La sintaxis PL/pgSQL es específica de PostgreSQL, que es el motor oficial y obligatorio del parcial (PostgreSQL 16 con asyncpg).
