# CHANGES — Secuencia de Implementación

> Índice canónico de todos los changes del proyecto **ParcialProg** (Librería con Acceso, Transacciones y Despliegue en VPS).
> Cada change es atómico: un agente puede implementarlo en una sesión (~4-6 horas).
> **Leer este archivo antes de ejecutar cualquier `/opsx:propose`.**

---

## Cómo usar este documento

1. Identificar el change a implementar (verificar que sus dependencias están en `openspec/changes/archive/`).
2. Leer los docs de la knowledge-base indicados en "Leer antes".
3. Ejecutar `/opsx:propose <nombre-del-change>`.
4. Al terminar el change, archivarlo con `/opsx:archive <nombre-del-change>`.
5. Marcar el checkbox `[x]` en este archivo.

---

## Árbol de dependencias

```
C-01 foundation-and-architecture
  │
  ├── C-09 docker-vps-deployment ──────────────────────────────────────┐
  │                                                                    │
  └── C-02 core-models-and-migrations                                  │
        │                                                              │
        ├── C-03 append-only-stock-trigger ──┐                         │
        │                                    │                         │
        └── C-04 auth-and-session            │                         │
              │                              │                         │
              ├── C-05 roles-and-admin       │                         │
              │                              │                         │
              └── C-06 catalog-and-inventory ◄                         │
                    │                                                  │
                    └── C-07 sales-and-transactions                    │
                          │                                            │
                          └── C-08 seed-and-error-hardening            │
                                │                                      │
                                └── C-10 e2e-evidence-and-packaging ◄──┘
```

### Paralelismo por fase

> Cada "gate" es un punto de sincronización. Los changes dentro de un grupo pueden ejecutarse en paralelo.

```
GATE 0: ninguna
  → C-01 (solo)

GATE 1: C-01 ✓
  → C-02 core-models-and-migrations    [Agente A]
  → C-09 docker-vps-deployment         [Agente C]

GATE 2: C-02 ✓                         ← FORK (Ramas Core e Inventario)
  → C-03 append-only-stock-trigger     [Agente B]
  → C-04 auth-and-session              [Agente A]

GATE 3: C-04 ✓
  → C-05 roles-and-admin-management    [Agente A]

GATE 4: C-03 + C-04 ✓
  → C-06 catalog-and-inventory         [Agente B — si C-03 ✓]

GATE 5: C-05 + C-06 ✓
  → C-07 sales-and-transactions        [Agente A]

GATE 6: C-07 ✓
  → C-08 seed-and-error-hardening      [Agente A]

GATE 7: C-08 + C-09 ✓
  → C-10 e2e-evidence-and-packaging    [Agente A]
```

### Camino crítico (7 changes — mínimo irreducible)

```
C-01 → C-02 → C-03 → C-06 → C-07 → C-08 → C-10
```

### Plan óptimo con 3 agentes

```
Paso │ Agente A (Backend Core / Auth) │ Agente B (Dominio / Catálogo) │ Agente C (Infra / Despliegue)
─────┼────────────────────────────────┼───────────────────────────────┼──────────────────────────────
  1  │ C-01 foundation-and-arch       │               —               │              —
  2  │ C-02 core-models-and-migrations│               —               │ C-09 docker-vps-deployment
  3  │ C-04 auth-and-session          │ C-03 append-only-stock-trigger│              —
  4  │ C-05 roles-and-admin-mgmt      │ C-06 catalog-and-inventory    │              —
  5  │ C-07 sales-and-transactions    │               —               │              —
  6  │ C-08 seed-and-error-hardening  │               —               │              —
  7  │ C-10 e2e-evidence-and-packaging│               —               │              —
```

---

## FASE 0 — Cimientos y Arquitectura Base

### [C-01] `foundation-and-architecture`
- **Estado**: `[x]` completado (archivado como `2026-11-07-foundation-and-architecture`)
- **Scope**: Scaffolding del monorepo en capas, configuración y endpoints de salud
  - Estructura de carpetas: `parcial/` (`app/core/`, `app/modules/health/`), `despliegue/`, `docs/`, `knowledge-base/`
  - Dependencias en `parcial/requirements.txt`: FastAPI 0.111, SQLModel 0.0.24, SQLAlchemy 2.0 async, asyncpg 0.30, Alembic 1.13, pydantic-settings 2.0, bcrypt 4.0, PyJWT 2.8, uvicorn
  - Configuración tipada en `parcial/app/core/config.py`: `Settings` con `pydantic-settings`, cálculo de `DATABASE_URL` asincrónica (`postgresql+asyncpg`), `SECRET_KEY`, `COOKIE_SECURE`, `SQL_ECHO`, lectura sin valores hardcodeados
  - Motor y sesiones asincrónicas en `parcial/app/core/database.py`: `create_async_engine`, `async_sessionmaker`, generador de dependencia `get_db`
  - Context manager Unit of Work base en `parcial/app/core/unit_of_work.py`: control de commit al éxito y rollback automático ante excepciones
  - Repositorio base en `parcial/app/core/repository.py`: `BaseRepository[T]` y `SoftDeleteRepository[T]` con operaciones genéricas async (`get`, `get_all`, `add`, `delete`), sólo `flush()`, nunca `commit()`
  - Envoltorio de paginación genérica en `parcial/app/core/paginacion.py`: `{items, total, page, size, pages}`
  - Aplicación FastAPI en `parcial/main.py`: ciclo de vida (lifespan) con precarga de configuraciones
  - Endpoints de salud en `parcial/app/modules/health/router.py`: `GET /health/live` (200 OK) y `GET /health/ready` (valida conexión viva a PostgreSQL)
  - Plantilla de variables en `parcial/env.example`
  - Tests unitarios de arranque y salud del servidor
- **Dependencias**: ninguna
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/01_vision_y_objetivos.md` §Objetivos de la arquitectura
  - `knowledge-base/02_descripcion_general.md` §Stack tecnológico
  - `knowledge-base/08_arquitectura_propuesta.md` §Patrones aplicados y Estructura de directorios
  - `knowledge-base/05_reglas_de_negocio.md` §Excepciones y Formatos Globales

---

## FASE 1 — Modelos Core y Restricciones de Base de Datos

### [C-02] `core-models-and-migrations`
- **Estado**: `[x]` completado (archivado como `2026-11-07-core-models-and-migrations`)
- **Scope**: Modelos de datos del parcial y baseline de migraciones Alembic
  - Modelos SQLModel de Seguridad en `parcial/app/modules/usuarios/models.py`: `Usuario`, `AsignacionRol`, `IntentoAcceso`, `EventoSeguridad`
  - Modelos SQLModel de Catálogo en `parcial/app/modules/`: `Editorial`, `Genero`, `Autor`, `LibroAutor`, `Libro` con `borrado_en` (`timestamptz` nullable) y constraints CHECK `precio > 0`, `stock >= 0`
  - Modelos SQLModel de Clientes en `parcial/app/modules/clientes/models.py`: `Cliente` con `usuario_id` (FK nullable, UNIQUE), `PerfilCliente`
  - Modelos SQLModel de Ventas en `parcial/app/modules/ventas/models.py`: `Venta`, `RenglonVenta`, `MovimientoStock` con CHECK `cantidad <> 0`
  - Configuración de Alembic en `parcial/alembic.ini` y `parcial/migrations/env.py` con driver asincrónico `asyncpg` y metadata unificada
  - Migración 0001: `0001_initial_tp.py` (esquema del TP Capítulos 1 a 4)
  - Migración 0002: `0002_parcial_modelos.py` con evolución de esquema:
    - Tablas nuevas `usuario`, `asignacion_rol`, `intento_acceso`, `evento_seguridad`, `movimiento_stock`
    - Columna `cliente.usuario_id` (FK nullable, UNIQUE)
    - Columna `libro.borrado_en` (`timestamptz` nullable)
    - Índice único parcial: `CREATE UNIQUE INDEX uq_asignacion_rol_abierta ON asignacion_rol (usuario_id, rol) WHERE revocada_en IS NULL;` (RN-03)
    - Índice único parcial: `CREATE UNIQUE INDEX uq_libro_isbn_vigente ON libro (isbn) WHERE borrado_en IS NULL;` (RN-01, RN-13)
    - Índice compuesto: `CREATE INDEX ix_intento_acceso_email_ip_cuando ON intento_acceso (email, ip, cuando);`
  - Tests: validación de ejecución limpia de `alembic upgrade head` y `downgrade base`
- **Dependencias**: C-01
- **Governance**: CRITICO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §Dominios, ERD y Entidades
  - `knowledge-base/05_reglas_de_negocio.md` §Catálogo y Unicidad, §Usuarios y Roles
  - `knowledge-base/08_arquitectura_propuesta.md` §Estructura de directorios
  - `knowledge-base/09_decisiones_y_supuestos.md` §Modelado relacional e Índices parciales

---

### [C-03] `append-only-stock-trigger`
- **Estado**: `[x]` completado (archivado como `2026-11-07-append-only-stock-trigger`)
- **Scope**: Disparador de inmutabilidad en PostgreSQL para movimientos de stock
  - Migración manual Alembic en `parcial/migrations/versions/0003_trigger_solo_agregado.py`:
    - Función PL/pgSQL: `fn_proteger_movimiento_stock_solo_agregado()` que eleva excepción fatal si `TG_OP` es `UPDATE` o `DELETE`
    - Trigger de base de datos: `tr_movimiento_stock_solo_agregado` ejecutado `BEFORE UPDATE OR DELETE ON movimiento_stock FOR EACH ROW` (RN-12)
    - Reversión en `downgrade()`: `DROP TRIGGER` y `DROP FUNCTION`
  - Script SQL de verificación `parcial/test/caso_c14_solo_agregado.sql`:
    - Inserción de movimiento de prueba
    - Intento de ejecución de `UPDATE` (falla rechazada por trigger)
    - Intento de ejecución de `DELETE` (falla rechazada por trigger)
    - Consulta de comprobación de persistencia intacta
  - Plantilla de salida y captura en `parcial/evidencia/c14_psql_output.txt`
  - Tests automatizados en pytest/asyncpg que validen el rechazo estricto de modificaciones físicas
- **Dependencias**: C-02
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §movimiento_stock
  - `knowledge-base/05_reglas_de_negocio.md` §RN-12 Tabla de Sólo Agregado
  - `knowledge-base/08_arquitectura_propuesta.md` §Patrón Append-Only Table con Trigger
  - `knowledge-base/09_decisiones_y_supuestos.md` §Garantías delegadas en PostgreSQL

---

## FASE 2 — Autenticación, Seguridad y Sesión

### [C-04] `auth-and-session`
- **Estado**: `[x]` completado (archivado como `2026-11-07-auth-and-session`)
- **Scope**: Autenticación segura con cookie HttpOnly, rate limiting y ciclo de vida de sesión
  - Módulo criptográfico en `parcial/app/core/security.py`:
    - Bcrypt asincrónico vía `asyncio.to_thread` protegido con `asyncio.Semaphore(4)` para no saturar el event loop
    - Creación y verificación de JWT (`PyJWT`) con claims: `sub`, `email`, `roles`, `iat`, `exp`
    - Dummy hash precomputado en lifespan para verificación en tiempo constante (RN-08)
  - Rate limiting e intentos en `parcial/app/modules/usuarios/` (`IntentoAccesoRepository`):
    - Registro de intento en sesión y transacción independiente confirmada de inmediato
    - Conteo de fallos en ventana de 60s por tupla `(email, ip)`: responde 429 con `Retry-After: 60` sin calcular hash si fallos >= 5 (RN-07)
  - Dependencias de seguridad en `parcial/app/core/dependencies.py`:
    - `get_usuario_actual`: extracción de JWT desde cookie `access_token` (no body ni headers) y validación de usuario activo en BD
    - `control_cambio_obligatorio`: interceptor que arroja 403 Forbidden a rutas fuera de `/auth` si `usuario.debe_cambiar_password == True` (RN-06)
    - `requiere_rol`: autorización resuelta en base contra `asignacion_rol` vigente por request (RN-04)
  - Endpoints en `parcial/app/modules/usuarios/router.py`:
    - `POST /auth/registro`: auto-registro atómico de usuario, asignacion_rol ('CLIENTE') y cliente en un solo Unit of Work (RN-02); validación password <= 72 bytes (422) y colisión de email (409)
    - `POST /auth/login`: login con emisión de cookie HttpOnly `access_token` (`SameSite=Lax`, `Max-Age=1800`), tiempo constante (RN-08)
    - `POST /auth/logout`: limpieza de cookie con `Max-Age=0`
    - `GET /auth/yo`: datos del usuario autenticado con roles vigentes en base y roles del token
    - `POST /auth/cambiar-password`: validación de clave previa, actualización de hash, `debe_cambiar_password = False`, y registro en `evento_seguridad` (RN-16)
  - Casos de prueba `.http`: `caso_c01_parametro_invalido.http`, `caso_c02_registro_conflictos.http`, `caso_c03_cookie_login.http`, `caso_c04_timing_login.http`, `caso_c05_rate_limit.http`, `caso_c09_cambio_obligatorio.http`
- **Dependencias**: C-02
- **Governance**: CRITICO
- **Leer antes**:
  - `knowledge-base/03_actores_y_roles.md` §Actores y Matriz RBAC
  - `knowledge-base/05_reglas_de_negocio.md` §Usuarios, Roles y Seguridad (RN-02..RN-08, RN-16)
  - `knowledge-base/06_funcionalidades.md` §Épica 1: Autenticación y Ciclo de Vida de Sesión
  - `knowledge-base/07_flujos_principales.md` §Flujo 1: Inicio de Sesión y §Flujo 3: Autorización por Petición
  - `knowledge-base/08_arquitectura_propuesta.md` §Off-Event-Loop Cryptography

---

### [C-05] `roles-and-admin-management`
- **Estado**: `[x]` completado (archivado como `2026-11-07-roles-and-admin-management`)
- **Scope**: Gestión administrativa de empleados, asignación/revocación de roles y auditoría
  - Endpoints administrativos en `parcial/app/modules/usuarios/router.py` (rol ADMIN):
    - `POST /usuarios`: alta de personal con contraseña provisoria y `debe_cambiar_password = True` (US-005), registrando en `evento_seguridad` (RN-16)
    - `GET /usuarios/{id}/roles`: consulta del historial y estado de roles del usuario
    - `POST /usuarios/{id}/roles`: asignación de rol con validación de zona horaria y futuro en `vence_en` (422), unicidad de rol abierto (RN-03, 409), cierre de rol vencido si aplica, y registro en `evento_seguridad` (RN-16)
    - `DELETE /usuarios/{id}/roles`: revocación lógica escribiendo `revocada_en = now()`, comprobando autoprotección administrativa (RN-05: no auto-revocarse rol ADMIN ni dejar el sistema sin administradores vigentes, 409), y registro en `evento_seguridad` (RN-16)
    - `GET /eventos`: consulta paginada del log de seguridad en `evento_seguridad`
  - Capa de servicio y repositorios: `UsuarioRepository`, `AsignacionRolRepository`, `EventoSeguridadRepository` coordinados vía `UnitOfWork`
  - Casos de prueba `.http`: `caso_c06_permisos_y_lo_propio.http`, `caso_c07_revocar_rol_en_vivo.http`, `caso_c08_autoproteccion_admin.http`
- **Dependencias**: C-04
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/03_actores_y_roles.md` §RBAC — Matriz de permisos
  - `knowledge-base/05_reglas_de_negocio.md` §RN-03, RN-04, RN-05, RN-16
  - `knowledge-base/06_funcionalidades.md` §Épica 2: Gestión de Personal, Roles y Auditoría
  - `knowledge-base/07_flujos_principales.md` §Flujo 3: Autorización por Petición

---

## FASE 3 — Dominio de Negocio: Catálogo, Stock y Ventas

### [C-06] `catalog-and-inventory`
- **Estado**: `[x]` completado (archivado como `2026-11-07-catalog-and-inventory`)
- **Scope**: Catálogo comercial, reposición de inventario y borrado lógico con reuso de ISBN
  - Módulos `editoriales`, `generos`, `autores` en `parcial/app/modules/`:
    - Schemas Pydantic, Repositorios (`EditorialRepository`, `GeneroRepository`, `AutorRepository`), Servicios y Routers
    - Endpoints públicos de lectura: `GET /editoriales`, `GET /generos`, `GET /autores`, `GET /{entidad}/{id}/libros` paginados
    - Endpoints administrativos (ADMIN): creación y edición con validación de unicidad de nombre (RN-01, 409)
  - Módulo `libros` en `parcial/app/modules/libros/`:
    - Repositorio `LibroRepository` (extiende `SoftDeleteRepository[Libro]` filtrando `borrado_en IS NULL`)
    - Repositorio `MovimientoStockRepository`
    - `POST /libros`: alta de libro recibiendo autores y `stock_inicial`, creando en una sola transacción el libro, asociaciones en `libro_autor` y el `movimiento_stock` ("Stock inicial") (RN-11, US-007)
    - `GET /libros` y `GET /libros/{id}`: catálogo público con paginación estándar `{items, total, page, size, pages}`, ocultando libros borrados lógicamente
    - `PATCH /libros/{id}`: modificación de título y precio; si se envía el campo `stock`, responde 422 rechazándolo (RN-11)
    - `POST /libros/{id}/reponer`: reposición de stock que incrementa `libro.stock` y registra `movimiento_stock` ("Reposición") en Unit of Work; si está borrado, responde 409 (RN-13)
    - `GET /libros/{id}/movimientos`: auditoría de stock (ADMIN)
    - `DELETE /libros/{id}`: baja lógica escribiendo `borrado_en = now()`, retornando 204 No Content; habilita la reutilización de ISBN para un nuevo libro gracias al índice único parcial (RN-13, US-009)
  - Casos de prueba `.http`: `caso_c13_reponer_baja_reuso_isbn.http`, `caso_c16_filtros_seguridad_paginacion.http`
- **Dependencias**: C-02, C-03
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §Catálogo, §libro, §movimiento_stock
  - `knowledge-base/05_reglas_de_negocio.md` §RN-01, RN-11, RN-12, RN-13
  - `knowledge-base/06_funcionalidades.md` §Épica 3: Catálogo, Inventario y Borrado Lógico
  - `knowledge-base/07_flujos_principales.md` §Flujo 4: Borrado Lógico y Reutilización de ISBN

---

### [C-07] `sales-and-transactions`
- **Estado**: `[x]` completado (archivado como `2026-11-07-sales-and-transactions`)
- **Scope**: Gestión de clientes, venta transaccional con descuento de stock, BackgroundTasks y resolución de N+1
  - Módulo `clientes` en `parcial/app/modules/clientes/`:
    - Repositorios `ClienteRepository` y `PerfilClienteRepository`
    - Endpoints para gestión de clientes por personal (ADMIN, VENDEDOR): `POST /clientes`, `GET /clientes/{id}`, `PATCH /clientes/{id}`, `POST /clientes/{id}/perfil`
    - Endpoint para consultar ventas de un cliente: `GET /clientes/{id}/ventas`
  - Módulo `ventas` en `parcial/app/modules/ventas/`:
    - Schemas Pydantic con validación de no repetidos en renglones (422)
    - Repositorios `VentaRepository`, `RenglonVentaRepository`
    - Servicio `VentasService` con orquestación transaccional en `UnitOfWork`:
      - `POST /ventas`: cálculo de total en servidor copiando precio actual del catálogo (RN-09); validación atómica de stock de cada libro; descuento de stock y creación de `movimiento_stock` ("Venta") por cada renglón; si algún libro tiene stock insuficiente o está dado de baja, rollback completo de la transacción y respuesta 409 (RN-10); disparo de comprobante asincrónico vía `BackgroundTasks` (`asyncio.sleep(0.5)`) que loguea tras commit exitoso
      - `GET /ventas`: listado general de ventas para personal (ADMIN, VENDEDOR) paginado
      - `GET /ventas/{id}`: consulta detallada con carga anticipada (eager loading `selectinload`/`joinedload`) de cliente, renglones y libros, resolviendo sin problema N+1 (RN-15, US-011); si el solicitante es CLIENTE, valida que `venta.cliente_id == cliente.id` de su cuenta, respondiendo 403 si intenta ver venta ajena (RN-14)
      - `GET /mis-ventas`: listado de compras paginadas del cliente autenticado (RN-14)
  - Casos de prueba `.http`: `caso_c10_venta_valida.http`, `caso_c11_venta_insuficiente.http`, `caso_c12_venta_inexistente.http`, `caso_c15_eager_loading_n1.http`
  - Evidencia N+1 en `parcial/evidencia/c15_consultas_n1_output.txt`
- **Dependencias**: C-03, C-04, C-06
- **Governance**: CRITICO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §Ventas e Inventario, §cliente
  - `knowledge-base/05_reglas_de_negocio.md` §RN-09, RN-10, RN-14
  - `knowledge-base/06_funcionalidades.md` §Épica 4: Ventas y Despacho Asincrónico
  - `knowledge-base/07_flujos_principales.md` §Flujo 2: Registro de una Venta Atómica
  - `knowledge-base/08_arquitectura_propuesta.md` §Patrón Unit of Work

---

## FASE 4 — Integración, Datos Iniciales y Resiliencia

### [C-08] `seed-and-error-hardening`
- **Estado**: `[x]` completado (archivado como `2026-11-07-seed-and-error-hardening`)
- **Scope**: Carga de datos iniciales requeridos por consigna y traducción global de excepciones de base
  - Script idempotente de inicialización en `parcial/seed.py`:
    - Usuarios requeridos: `admin@example.com` (ADMIN), `admin2@example.com` (ADMIN), `vendedor@example.com` (VENDEDOR), `ana@example.com` (CLIENTE vinculada a ficha Ana Paz), `nuevo@example.com` (VENDEDOR con `debe_cambiar_password = True`)
    - Catálogo: 3 editoriales, 3 géneros, 6 autores, 5 libros con stock inicial y movimientos (`Rayuela`, `Antología de la literatura fantástica`, `Ficciones`, `Respiración artificial`, `Bestiario`)
    - Clientes: Lucía Fernández (con perfil), Tomás Ríos (sin perfil), Ana Paz (con usuario)
    - Venta 1 histórica: Lucía Fernández con `vendedor@example.com`, renglones (1 Rayuela + 2 Ficciones, total 69000.00), movimientos de stock de salida correspondientes (-1, -2)
    - Historial de seguridad: registro inicial con `actor = 'SISTEMA'` y `accion = 'Carga de los datos iniciales'` en `evento_seguridad`
  - Manejo global de excepciones en `parcial/app/core/exceptions.py` y `main.py`:
    - Middleware/Exception handler para `IntegrityError` de SQLAlchemy: traducción limpia a HTTP 409 con mensaje de negocio, ocultando trazas, nombres de constraints o texto de PostgreSQL (RN-01, RN-15)
    - Handler de validación `RequestValidationError`: HTTP 422 estandarizado
    - Captura global de errores no controlados para prevenir 500 descontrolados
  - Tests: validación de ejecución de `seed.py` y comprobación de respuestas 409 en violaciones de unicidad
- **Dependencias**: C-05, C-07
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §Seed data inicial requerido
  - `knowledge-base/05_reglas_de_negocio.md` §RN-01 Unicidad y §RN-15 Ocultamiento de Detalles Internos
  - `knowledge-base/08_arquitectura_propuesta.md` §Layered Architecture
  - `knowledge-base/09_decisiones_y_supuestos.md` §Manejo de Errores e Invariantes

---

## FASE 5 — Despliegue Docker VPS y Verificación E2E

### [C-09] `docker-vps-deployment`
- **Estado**: `[x]` completado (archivado como `2026-11-08-docker-vps-deployment`)
- **Scope**: Empaquetado Docker Alpine del TP Capítulos 1 a 4 y documentación para VPS
  - Código fuente del TP Capítulos 1 a 4 aislado en carpeta `despliegue/` (sin cambios del parcial)
  - `despliegue/Dockerfile`:
    - Imagen base `python:3.12-alpine` optimizada (< 100 MB, ~74.7 MB)
    - Usuario sin privilegios `appuser` y ejecución segura con directiva `USER appuser`
    - Instalación de dependencias con `--no-cache-dir`
    - HEALTHCHECK configurado con `wget -qO- http://127.0.0.1:8000/health/ready` (usando IP explícita 127.0.0.1 para evitar IPv6 `::1` en Alpine)
    - Script de arranque: ejecución de `alembic upgrade head` y posterior inicio de Uvicorn en `0.0.0.0:8000`
  - `despliegue/.dockerignore`: exclusión de `.env`, `.git`, `__pycache__`, `.venv`, `*.pyc`
  - `despliegue/env.example`: plantilla limpia de configuración sin credenciales hardcodeadas
  - Guía operativa `despliegue/DEPLOY.md`: comandos de build, flags de ejecución (`--add-host=host.docker.internal:host-gateway`), estrategia de upgrade sin pérdida de datos, y plantilla de evidencia D-01 a D-08
  - Archivos y scripts para captura de evidencias en `despliegue/evidencia/`:
    - `d01_docker_images.txt` (tamaño de imagen)
    - `d02_docker_ps_healthy.txt` (estado healthy del contenedor)
    - `d03_external_requests.txt` (peticiones remotas curl)
    - `d04_container_recreation.txt` (recreación manteniendo datos)
    - `d05_missing_database_url.txt` (falla esperada sin env vars)
    - `d06_no_secrets_in_image.txt` (auditoría de secretos en imagen)
    - `d07_non_root_user.txt` (verificación de uid appuser)
    - `d08_background_tasks_logs.txt` (logs de background tasks)
- **Dependencias**: C-01
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/02_descripcion_general.md` §Entregables
  - `knowledge-base/08_arquitectura_propuesta.md` §Estructura despliegue/
  - `knowledge-base/11_despliegue_docker_vps.md` §Requisitos Docker y §Documentación y Evidencia
  - `knowledge-base/09_decisiones_y_supuestos.md` §Despliegue y VPS

---

### [C-10] `e2e-evidence-and-packaging`
- **Estado**: `[x]` completado (archivado como `2026-11-08-e2e-evidence-and-packaging`)
- **Scope**: Verificación integral de la suite de pruebas `.http`, recolección de evidencias y empaquetado final
  - Ejecución integral de la suite de pruebas `.http` (`parcial/test/caso_c01` a `caso_c16`) contra base con seed
  - Recolección final de evidencias en `parcial/evidencia/`: `c14_psql_output.txt` y `c15_consultas_n1_output.txt`
  - Ejecución y recolección final de evidencias de Docker en `despliegue/evidencia/` (`d01` a `d08`)
  - Redacción de `parcial/README.md` con instrucciones de puesta en marcha, endpoints, roles y arquitectura
  - Preparación de script/procedimiento de empaquetado del archivo final `Parcial_Cap1a6_<NombreDelGrupo>.zip` conteniendo únicamente `parcial/` y `despliegue/`, excluyendo `.venv`, `__pycache__`, `.env` y archivos temporales
- **Dependencias**: C-08, C-09
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §Criterios de aceptación
  - `knowledge-base/07_flujos_principales.md` §Flujos E2E
  - `knowledge-base/11_despliegue_docker_vps.md` §Evidencia y Casos D-01 a D-08
  - `knowledge-base/10_preguntas_abiertas.md` §Preguntas de entrega y empaquetado
