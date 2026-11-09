# Tasks

## 1. Modelos de Dominio por Módulo

- [x] 1.1 Implementar modelos de Seguridad en `parcial/app/modules/usuarios/models.py`: `Usuario`, `AsignacionRol` (con CHECK y partial index), `IntentoAcceso` (con índice compuesto) y `EventoSeguridad`.
- [x] 1.2 Implementar modelos de Catálogo en `parcial/app/modules/editoriales/models.py`, `generos/models.py`, `autores/models.py`, y `libros/models.py` (`LibroAutor` y `Libro` con `borrado_en` e índice único parcial).
- [x] 1.3 Implementar modelos de Clientes en `parcial/app/modules/clientes/models.py`: `Cliente` (con `usuario_id` y relación escalar `usuario`) y `PerfilCliente`.
- [x] 1.4 Implementar modelos de Ventas e Inventario en `parcial/app/modules/ventas/models.py`: `Venta`, `RenglonVenta` y `MovimientoStock` (con CHECK `cantidad <> 0`).

## 2. Configuración de Alembic y Migraciones Versionadas

- [x] 2.1 Configurar `parcial/alembic.ini` y `parcial/migrations/env.py` con soporte asincrónico para `asyncpg` y metadata unificada.
- [x] 2.2 Crear migración `parcial/migrations/versions/0001_initial_tp.py` con el esquema base de los capítulos 1 a 4 y comentario explicativo.
- [x] 2.3 Crear migración `parcial/migrations/versions/0002_parcial_modelos.py` con tablas de seguridad, movimientos de stock, borrado lógico e índices parciales, con comentario explicativo.

## 3. Verificación Automatizada

- [x] 3.1 Implementar suite de pruebas en `parcial/test/test_models.py` validando definición de tablas, relaciones escalares, restricciones CHECK e índices.
- [x] 3.2 Ejecutar suite de pruebas con pytest y verificar que todos los casos pasen.

## Workflow follow-up

- Validar change con `openspec validate --strict`.
- Archivar change con `openspec archive core-models-and-migrations -y`.
- Actualizar `CHANGES.md`.
