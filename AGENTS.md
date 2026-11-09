# ParcialProg — Instrucciones para Agentes

> Este archivo (y su copia `CLAUDE.md`) es lo PRIMERO que todo agente lee al entrar al repo.
> Generado a partir de `knowledge-base/`, `CHANGES.md` y `.atl/skill-registry.md`. No editar a mano sin re-sincronizar ambos archivos.

---

## Stack Tecnológico

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

Detalle completo: [knowledge-base/02_descripcion_general.md](knowledge-base/02_descripcion_general.md)

---

## Base de Conocimiento

La fuente de verdad del dominio vive en `knowledge-base/`. **Leé el archivo relevante ANTES de implementar.**

| Archivo | Cuándo leerlo |
|---|---|
| [01_vision_y_objetivos.md](knowledge-base/01_vision_y_objetivos.md) | Entender propósito y alcance v6.0 |
| [02_descripcion_general.md](knowledge-base/02_descripcion_general.md) | Stack, capas y grupos de rutas |
| [03_actores_y_roles.md](knowledge-base/03_actores_y_roles.md) | Auth, RBAC, matriz de permisos y rutas públicas |
| [04_modelo_de_datos.md](knowledge-base/04_modelo_de_datos.md) | Entidades, ERD, restricciones, índices y seed inicial |
| [05_reglas_de_negocio.md](knowledge-base/05_reglas_de_negocio.md) | Reglas codificadas RN-01 a RN-16 y garantes |
| [06_funcionalidades.md](knowledge-base/06_funcionalidades.md) | Historias de usuario y criterios de aceptación |
| [07_flujos_principales.md](knowledge-base/07_flujos_principales.md) | Flujos E2E (login, ventas, permisos, borrado lógico) |
| [08_arquitectura_propuesta.md](knowledge-base/08_arquitectura_propuesta.md) | Patrones, estructura de directorios y env vars |
| [09_decisiones_y_supuestos.md](knowledge-base/09_decisiones_y_supuestos.md) | Decisiones de diseño (DD-01..04) y supuestos |
| [10_preguntas_abiertas.md](knowledge-base/10_preguntas_abiertas.md) | Parámetros del grupo y del VPS |
| [11_despliegue_docker_vps.md](knowledge-base/11_despliegue_docker_vps.md) | Requisitos Dockerfile Alpine y evidencia D-01 a D-08 |

---

## Skills Disponibles

| Agente | Rol | Skills que carga |
|---|---|---|
| **Backend Core** | FastAPI / SQLModel / UoW / Repositorios | `fastapi`, `fastapi-templates`, `postgresql-table-design`, `endpoint-code-review` |
| **Seguridad y DB** | Auth / RBAC / Postgres triggers e índices | `auth-implementation-patterns`, `postgresql-table-design` |
| **DevOps y Despliegue** | Docker / VPS / Alpine / Healthcheck | `docker-compose-patterns` |
| **Orquestación** | SDD / OPSX / Foundation | `active-orchestrator`, `kb-creator`, `roadmap-generator`, `agents-md-generator`, `skill-registry` |

Cargá la skill correspondiente al contexto ANTES de escribir código.

> Los compact rules de cada skill los resuelve el orquestador desde `.atl/skill-registry.md` (generado por `skill-registry`; no versionado — no está en el repo). Esta tabla solo mapea skill→rol.

---

## Roadmap de Changes

El plan de implementación completo está en [CHANGES.md](CHANGES.md). Resumen:

- **Total**: 10 changes en 6 fases.
- **Camino crítico** (7): `C-01 → C-02 → C-03 → C-06 → C-07 → C-08 → C-10`.
- **Primer change**: `C-01` (`foundation-and-architecture`).

**Antes de cualquier `/opsx:propose`**: leé [CHANGES.md](CHANGES.md), identificá las dependencias del change y los archivos de "Leer antes".

---

## Reglas Duras (específicas del proyecto)

> Reglas **globales** ya definidas en el entorno (orquestador, governance, TDD, engram): el proyecto las **hereda**, no se repiten acá.

Acá van las reglas específicas de este proyecto, derivadas de su stack (Python 3.12, FastAPI, SQLModel, PostgreSQL 16, Alembic, Docker Alpine) y **confirmadas con el usuario**. Son contrato; romperlas es un defecto. Formato `NUNCA X → hacer Y`:

### Modelado, Esquema y Persistencia
- NUNCA usar `create_all()` → el esquema se crea y evoluciona exclusivamente con migraciones de Alembic (`alembic upgrade head`).
- NUNCA usar `float` para montos monetarios o totales → usar siempre `Decimal` en Python y `Numeric(10, 2)` o `Numeric(12, 2)` en PostgreSQL.
- NUNCA definir un `UNIQUE` común para `isbn` en `libro` ni para `(usuario_id, rol)` en `asignacion_rol` → usar siempre índices únicos parciales condicionales (`postgresql_where="borrado_en IS NULL"` y `postgresql_where="revocada_en IS NULL"`).
- NUNCA modelar `Cliente.usuario` como una lista → debe ser una relación escalar (1 a 1 opcional) que devuelva un objeto o `None`.
- NUNCA omitir índices en claves foráneas → toda Foreign Key en PostgreSQL debe tener su índice explícito creado.

### Repositorios y Unit of Work
- NUNCA llamar a `session.commit()` dentro de un repositorio ni en un servicio → solo `add()` y `update()` hacen `flush()`. El `commit()` o `rollback()` lo realiza exclusivamente el `UnitOfWork` en `__aexit__`.
- NUNCA instanciar `UnitOfWork` directamente dentro del servicio → el router lo construye mediante inyección de dependencias (`Depends`) y se lo pasa al servicio sin abrirlo; el servicio lo abre con `async with uow:`.
- NUNCA cerrar la sesión dentro del `UnitOfWork` → la sesión la gestiona el ciclo de vida del request (`get_session`).
- NUNCA modificar el stock de un libro mediante `PATCH` → el stock es una invariante que equivale a la suma de sus movimientos y solo cambia mediante `movimiento_stock` (alta inicial, reposición, ventas).
- NUNCA permitir que la tabla `movimiento_stock` admita `UPDATE` o `DELETE` → la tabla es estrictamente de sólo agregado, protegida por un disparador en PostgreSQL.

### Autenticación, Criptografía y Sesión
- NUNCA ejecutar funciones de hash de contraseñas (`bcrypt`) de forma sincrónica en el bucle de eventos → ejecutarlas mediante `asyncio.to_thread` bajo un semáforo de concurrencia (`asyncio.Semaphore`).
- NUNCA aceptar contraseñas mayores a 72 bytes en contratos de entrada de auth → validar explícitamente `len(v.encode('utf-8')) <= 72` para responder 422 y evitar que bcrypt lance excepciones de 500.
- NUNCA almacenar secretos, contraseñas o secret keys por defecto en el código, `.env`, `alembic.ini` o repositorio → si faltan en las variables de entorno, la aplicación no debe arrancar.
- NUNCA devolver el token JWT en el cuerpo del login ni leerlo de la cabecera `Authorization: Bearer` → viaja y se lee exclusivamente en la cookie `access_token` (`HttpOnly`, `SameSite=Lax`).
- NUNCA compartir la transacción de la petición para registrar intentos de acceso en `intento_acceso` → debe ejecutarse en una sesión y transacción independientes confirmadas de inmediato, con comentario obligatorio justificándolo.

### Contratos, Rutas y Respuestas
- NUNCA omitir `extra = "forbid"` en los esquemas de entrada de Pydantic → rechazar campos no declarados con 422.
- NUNCA incluir `password_hash` en ningún contrato de respuesta HTTP.
- NUNCA filtrar nombres de tablas, columnas o mensajes de error internos de PostgreSQL al cliente → capturar `IntegrityError` y traducirlos a 409 con mensaje de negocio. Ninguna entrada inválida debe terminar en 500.
- NUNCA omitir el envoltorio estándar de paginación `{items, total, page, size, pages}` → `page` inicia en 1, `size` entre 1 y 100; si se solicita una página superior a la última, responder 422.

### Contenedor y Despliegue
- NUNCA usar imágenes base pesadas para el contenedor → la imagen base debe ser estrictamente `python:3.12-alpine` (< 100 MB).
- NUNCA ejecutar el proceso del contenedor como usuario `root` → crear y activar un usuario sin privilegios (`USER appuser`).
- NUNCA configurar el HEALTHCHECK de Docker apuntando a `localhost` en Alpine → usar explícitamente `http://127.0.0.1:8000/health/ready` para evitar resolución a IPv6.

---

## Flujo de Trabajo

```
1. Leer la KB relevante (knowledge-base/)        → entender el dominio
2. Identificar el change en CHANGES.md           → respetar dependencias
3. /opsx:propose C-NN-nombre                     → proposal + design + specs + tasks
4. Implementar las tasks (cargando skills)       → respetando las reglas duras
5. /opsx:archive C-NN-nombre + marcar [x]        → cerrar el change
```

Aplicar TODAS las reglas duras en cada paso. Ante conflicto entre la KB y este archivo, las reglas duras prevalecen.
