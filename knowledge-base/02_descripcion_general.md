# Descripción General

## Stack tecnológico

| Capa / Componente | Tecnología | Versión mínima | Propósito |
|---|---|---|---|
| Lenguaje | Python | 3.12 | Lenguaje de desarrollo principal |
| Framework Web | FastAPI | 0.111 | Framework asincrónico para API REST (todos los handlers con `async def`) |
| Modelado ORM | SQLModel / Pydantic | 0.0.24 | Modelos de datos para tablas y contratos de entrada/salida |
| Persistencia y Async | SQLAlchemy | 2.0 (asincrónico) | Motor, fábrica de sesiones y carga anticipada (`selectinload`/`joinedload`) |
| Driver DB | asyncpg | 0.30 | Driver asincrónico nativo para PostgreSQL |
| Base de Datos | PostgreSQL | 16 | Motor relacional con soporte para triggers, índices parciales y tipos `timestamptz`/`numeric` |
| Migraciones | Alembic | 1.13 | Plantilla asincrónica para evolución de esquema versionado |
| Configuración | pydantic-settings | 2.0 | Tipado de variables de entorno con `@computed_field` sin secretos por defecto |
| Hashing | bcrypt | 4.0 | Hash de contraseñas ejecutado en thread pool con límite de concurrencia |
| Tokens | PyJWT | 2.8 | Generación y validación de tokens JWT en cookie `HttpOnly` |
| Servidor ASGI | Uvicorn | `fastapi[standard]` | Servidor ASGI para ejecución asincrónica |
| Contenedores | Docker | 20.10+ | Empaquetado sobre imagen base `python:3.12-alpine` |

## Arquitectura general

La aplicación sigue una arquitectura en capas estrictamente desacoplada:

```
[ Petición HTTP ]
       │
       ▼
 ┌───────────┐
 │  Router   │ ◄── Dependencias (get_session, get_current_user, require_role, get_uow)
 └─────┬─────┘
       │  (pasa DTOs validados y Unit of Work cerrado)
       ▼
 ┌───────────┐
 │  Service  │ ◄── Reglas de negocio (abre `async with uow:`, orquesta repositorios)
 └─────┬─────┘
       │
       ▼
 ┌───────────────┐
 │ Unit of Work  │ ◄── Coordina repositorios bajo una misma sesión (flush(), no commit())
 └─────┬─────────┘
       │
       ▼
 ┌───────────────┐
 │ Repositories  │ ◄── BaseRepository / SoftDeleteRepository (consultas con eager loading)
 └─────┬─────────┘
       │
       ▼
 ┌───────────────┐
 │ PostgreSQL 16 │ ◄── Restricciones CHECK, índices parciales, trigger append-only
 └───────────────┘
```

## Integraciones externas

| Componente | Tipo | Propósito |
|---|---|---|
| PostgreSQL 16 | Conexión TCP asincrónica (`postgresql+asyncpg`) | Persistencia relacional, garantías de integridad y disparadores |
| Tareas en Segundo Plano | `fastapi.BackgroundTasks` | Simulación no bloqueante del envío de comprobante de venta (`asyncio.sleep(0.5)`) |
| Docker Host / VPS | Despliegue en contenedor | Alojamiento en entorno de producción sin secretos |

## API REST — Resumen de grupos de rutas

- **Grupo Abierto**: Rutas que no requieren autenticación (catálogo público de libros, autores, editoriales, géneros, healthchecks `/health/live`, `/health/ready`, y endpoints de `/auth/registro`, `/auth/login`, `/auth/logout`).
- **Grupo Protegido**: Rutas que requieren sesión activa (`access_token` en cookie). Tienen montada a nivel router la verificación de `debe_cambiar_password` (RN-06), impidiendo el acceso a operaciones si el usuario tiene contraseña provisoria pendiente de cambio.
