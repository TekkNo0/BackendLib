# Arquitectura Propuesta

## Patrones aplicados

| Patrón | Dónde se aplica | Propósito y justificación |
|---|---|---|
| **Layered Architecture (Capas limpias)** | Toda la aplicación (`Router` → `Service` → `UoW` → `Repository` → `Model`) | Separación estricta de responsabilidades: los routers manejan HTTP y traducción de errores; los servicios orquestan negocio; los repositorios aíslan SQL. |
| **Unit of Work (UoW)** | `app/core/unit_of_work.py` y `app/modules/*/unit_of_work.py` | Context manager asincrónico que agrupa múltiples repositorios bajo una misma sesión de base de datos; ejecuta `commit()` al salir con éxito o `rollback()` ante excepciones. |
| **Repository Pattern** | `app/core/repository.py` (`BaseRepository[T]`, `SoftDeleteRepository[T]`) | Abstracción de acceso a datos sin acoplar lógica de persistencia; hace `flush()`, nunca `commit()`. |
| **Dependency Injection** | FastAPI `Depends` | Provisión de sesión única por request, usuario autenticado, verificación de roles vigentes y Unit of Work. |
| **Append-Only Table con Trigger** | Tabla `movimiento_stock` en PostgreSQL | Garantía a nivel motor de base de datos de que ningún movimiento de stock pueda ser actualizado ni eliminado. |
| **Off-Event-Loop Cryptography** | `app/core/security.py` | Ejecución de funciones de hash intensivas (`bcrypt`) mediante `asyncio.to_thread` protegidas por un `asyncio.Semaphore` para prevenir saturación del pool de threads. |

## Estructura de directorios del proyecto

La consigna exige organizar el entregable en dos carpetas dentro de la raíz:

```
ParcialProg/
├── parcial/
│   ├── main.py
│   ├── seed.py
│   ├── requirements.txt
│   ├── env.example
│   ├── alembic.ini
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── security.py
│   │   │   ├── dependencies.py
│   │   │   ├── repository.py
│   │   │   ├── paginacion.py
│   │   │   └── unit_of_work.py
│   │   └── modules/
│   │       ├── health/
│   │       │   └── router.py
│   │       ├── usuarios/
│   │       │   ├── models.py, schemas.py, repository.py, unit_of_work.py, service.py, router.py
│   │       ├── editoriales/
│   │       │   ├── models.py, schemas.py, repository.py, unit_of_work.py, service.py, router.py
│   │       ├── generos/
│   │       │   ├── models.py, schemas.py, repository.py, unit_of_work.py, service.py, router.py
│   │       ├── autores/
│   │       │   ├── models.py, schemas.py, repository.py, unit_of_work.py, service.py, router.py
│   │       ├── libros/
│   │       │   ├── models.py, schemas.py, repository.py, unit_of_work.py, service.py, router.py
│   │       ├── clientes/
│   │       │   ├── models.py, schemas.py, repository.py, unit_of_work.py, service.py, router.py
│   │       └── ventas/
│   │           ├── models.py, schemas.py, repository.py, unit_of_work.py, service.py, router.py
│   ├── migrations/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │       ├── 0001_initial_tp.py
│   │       ├── 0002_parcial_modelos.py
│   │       └── 0003_trigger_solo_agregado.py
│   ├── test/
│   │   ├── caso_c01_parametro_invalido.http
│   │   ├── caso_c02_registro_conflictos.http
│   │   ├── caso_c03_cookie_login.http
│   │   ├── caso_c04_timing_login.http
│   │   ├── caso_c05_rate_limit.http
│   │   ├── caso_c06_permisos_y_lo_propio.http
│   │   ├── caso_c07_revocar_rol_en_vivo.http
│   │   ├── caso_c08_autoproteccion_admin.http
│   │   ├── caso_c09_cambio_obligatorio.http
│   │   ├── caso_c10_venta_valida.http
│   │   ├── caso_c11_venta_insuficiente.http
│   │   ├── caso_c12_venta_inexistente.http
│   │   ├── caso_c13_reponer_baja_reuso_isbn.http
│   │   ├── caso_c14_solo_agregado.sql
│   │   ├── caso_c15_eager_loading_n1.http
│   │   └── caso_c16_filtros_seguridad_paginacion.http
│   ├── evidencia/
│   │   ├── c14_psql_output.txt
│   │   └── c15_consultas_n1_output.txt
│   └── README.md
│
├── despliegue/
│   ├── (Código TP Capítulos 1 a 4)
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── env.example
│   ├── DEPLOY.md
│   └── evidencia/
│       ├── d01_docker_images.txt
│       ├── d02_docker_ps_healthy.txt
│       ├── d03_external_requests.txt
│       ├── d04_container_recreation.txt
│       ├── d05_missing_database_url.txt
│       ├── d06_no_secrets_in_image.txt
│       ├── d07_non_root_user.txt
│       └── d08_background_tasks_logs.txt
```

## Variables de entorno requeridas

| Variable | Descripción | Tipo / Formato | Sensible |
|---|---|---|---|
| `POSTGRES_USER` | Usuario de PostgreSQL | Cadena (ej. `postgres`) | No |
| `POSTGRES_PASSWORD` | Contraseña de PostgreSQL | Cadena | **Sí** |
| `POSTGRES_DB` | Nombre de la base de datos | Cadena (ej. `libreria`) | No |
| `POSTGRES_HOST` | Host o IP del servidor PostgreSQL | Cadena (ej. `localhost` o IP) | No |
| `POSTGRES_PORT` | Puerto de conexión PostgreSQL | Entero (ej. `5432`) | No |
| `DATABASE_URL` | URL calculada con `postgresql+asyncpg` | `@computed_field` derivado | **Sí** |
| `SECRET_KEY` | Clave secreta para firma de JWT | Cadena aleatoria de 32+ bytes | **Sí** |
| `BCRYPT_ROUNDS` | Factor de costo computacional de bcrypt | Entero (ej. `12`) | No |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Duración del JWT emitido en minutos | Entero (ej. `30`) | No |
| `COOKIE_SECURE` | Flag Secure de cookie (para HTTPS en prod) | Booleano (ej. `False` en local, `True` en prod) | No |
| `SQL_ECHO` | Logging de consultas SQL en consola | Booleano (ej. `True` para diagnóstico) | No |
