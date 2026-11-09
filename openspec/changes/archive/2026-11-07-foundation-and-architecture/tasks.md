# Tasks

## 1. Scaffolding y Configuración Base

- [x] 1.1 Crear el árbol de directorios de entrega en `parcial/` (`app/core/`, `app/modules/health/`, `test/`) y verificar existencia.
- [x] 1.2 Crear `parcial/requirements.txt` y `parcial/env.example` documentando todas las variables requeridas y verificar que no contengan secretos.
- [x] 1.3 Implementar `parcial/app/core/config.py` con `Settings` (pydantic-settings), `@computed_field` para `DATABASE_URL` y verificar fallo si faltan contraseñas o claves.

## 2. Persistencia y Ciclo de Vida Asincrónico

- [x] 2.1 Implementar `parcial/app/core/database.py` con funciones constructoras de motor (`create_async_engine`), fábrica de sesiones (`async_sessionmaker`) y generador `get_session` con `expire_on_commit=False`.
- [x] 2.2 Implementar `parcial/app/core/repository.py` con `BaseRepository[T]` y `SoftDeleteRepository[T]`, verificando que solo invoquen `flush()` y nunca `commit()`.
- [x] 2.3 Implementar `parcial/app/core/unit_of_work.py` con el context manager asincrónico `UnitOfWork` base y verificar commit en éxito y rollback en error.
- [x] 2.4 Implementar `parcial/app/core/paginacion.py` con el esquema `{items, total, page, size, pages}` y validación HTTP 422 para páginas fuera de rango.

## 3. Módulo Health, Lifespan y Verificación

- [x] 3.1 Implementar `parcial/app/modules/health/router.py` con endpoints `GET /health/live` (200 OK) y `GET /health/ready` (SELECT 1 y 503 ante fallo de conexión).
- [x] 3.2 Implementar `parcial/main.py` con ciclo de vida `lifespan` configurando motor, fábrica de sesiones y hash ficticio en `app.state`, junto con `engine.dispose()` en el shutdown.
- [x] 3.3 Crear suite de pruebas en `parcial/test/test_foundation.py` y archivo `parcial/test/health.http` verificando `/health/live` y `/health/ready`.

## Workflow follow-up

- Verificar `openspec validate` sobre el change `foundation-and-architecture`.
- Implementar los archivos correspondientes a las tareas.
- Proceder con el testeo y archivo del change para desbloquear el Gate 1 (`C-02` y `C-09`).
