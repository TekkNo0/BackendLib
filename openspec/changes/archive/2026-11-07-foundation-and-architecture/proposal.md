# Proposal: Foundation and Architecture

## Why
El parcial requiere una arquitectura limpia en capas (Router → Service → UoW → Repository → Model) y un ciclo de vida robusto donde los recursos asincrónicos (motor de base de datos y fábrica de sesiones) se inicialicen dentro del `lifespan` de FastAPI y se guarden en `app.state` (Ejercicio 1 y Ejercicio 6). Sin estos cimientos de infraestructura, configuración y persistencia base, no es posible construir los modelos de dominio, las migraciones de Alembic, ni los módulos de autenticación y ventas.

## What Changes
- Creación de la estructura de entrega `parcial/` con su árbol modular canónico.
- Definición de dependencias mínimas en `parcial/requirements.txt` (FastAPI 0.111, SQLModel 0.0.24, SQLAlchemy 2.0 async, asyncpg 0.30, Alembic 1.13, pydantic-settings 2.0, bcrypt 4.0, PyJWT 2.8, uvicorn).
- Configuración con `pydantic-settings` en `parcial/app/core/config.py`: variables tipadas, `@computed_field` para `DATABASE_URL` con driver `postgresql+asyncpg`, sin secretos por defecto (si faltan `POSTGRES_PASSWORD` o `SECRET_KEY`, la app no arranca).
- Inicialización asincrónica en `parcial/app/core/database.py`: funciones que crean el motor y la fábrica de sesiones, generador `get_session` por petición con `expire_on_commit=False`.
- `BaseRepository[T]` y `SoftDeleteRepository[T]` en `parcial/app/core/repository.py`: constructor que recibe la sesión y la clase del modelo; métodos `get_by_id`, `get_all`, `count`, `add`, `update`, `delete`, `soft_delete`, `get_by_id_including_deleted`. Con `flush()`, nunca `commit()`.
- `UnitOfWork` base en `parcial/app/core/unit_of_work.py`: gestor de contexto asincrónico que confirma en `__aexit__`, revierte ante excepciones y no cierra la sesión.
- Envoltorio de paginación estandarizada en `parcial/app/core/paginacion.py`: `{items, total, page, size, pages}` con validación de rango (422).
- Módulo `health` en `parcial/app/modules/health/router.py`: `GET /health/live` (200 OK) y `GET /health/ready` (ejecuta `SELECT 1`, responde 503 si la base no responde).
- `parcial/main.py`: aplicación FastAPI con `lifespan` que inicializa motor, fábrica de sesiones y hash ficticio en `app.state`, ejecuta `dispose()` al apagar, y monta los grupos de rutas.
- Plantilla `parcial/env.example` con todas las variables declaradas y ningún secreto.

## Capabilities

### New Capabilities
- `system-foundation`: Inicialización y configuración del sistema, gestión de ciclo de vida del motor/sesiones asincrónicas en `lifespan` (`app.state`), endpoints de salud (`/health/live` y `/health/ready`), repositorios genéricos base (`BaseRepository` y `SoftDeleteRepository`), gestor de transacciones `UnitOfWork` base y esquema de paginación canónico.

### Modified Capabilities
Ninguna (este es el primer change del sistema).

## Impact
- Establece la estructura de código fuente `parcial/` y el estándar que consumirán todos los módulos subsiguientes.
- Habilita la ejecución de pruebas de salud (`GET /health/live` y `GET /health/ready`).
