# Design: Roles and Admin Management

## Context
El parcial establece que los roles no se guardan como columna en la tabla `usuario`, sino en filas de `asignacion_rol` con vigencia temporal (Páginas 6 y 11). La autorización no se decide a partir de los roles contenidos en el token JWT (que son puramente informativos), sino consultando en la base de datos en cada petición HTTP (RN-04). Además, se requiere autoprotección para evitar que el sistema quede sin administradores o que un administrador se revoque a sí mismo (RN-05), y una división limpia en dos grupos de rutas en `main.py` para bloquear a los usuarios con cambio obligatorio de contraseña (RN-06).

## Goals / Non-Goals

**Goals:**
- `get_usuario_actual`: obtiene el usuario autenticado consultando la base de datos con la misma sesión de la petición (401 si no hay cookie, token inválido o usuario inactivo).
- `requiere_rol(*roles)`: consulta roles vigentes en `asignacion_rol` en la base de datos en cada petición (RN-04).
- `control_cambio_password_obligatorio`: montado como dependencia del grupo protegido en `main.py` (RN-06).
- Endpoints de administración:
  - `POST /usuarios`: alta de personal con contraseña provisoria (`debe_cambiar_password=True`) y auditoría (RN-16).
  - `GET /usuarios/{id}/roles`: listado de roles con vigencia.
  - `POST /usuarios/{id}/roles`: asignación de rol validando fecha futura con zona horaria (422) y unicidad abierta (RN-03).
  - `DELETE /usuarios/{id}/roles/{rol}`: revocación de rol con autoprotección (RN-05).
  - `GET /eventos`: consulta paginada de auditoría para ADMIN.

**Non-Goals:**
- Control de pertenencia de ventas (`/mis-ventas` y comprobación de dueño en `GET /ventas/{id}`) — asignado a C-07.
- Operaciones sobre el catálogo de libros — asignado a C-06.

## Decisions

### D1: Consulta en Base de Datos en Cada Petición (`RN-04`)
- **Decisión**: La dependencia `requiere_rol(*roles_permitidos)` no confía en los roles empaquetados en el JWT. Realiza un `select(AsignacionRol.rol)` en la base filtrando `revocada_en IS NULL` y `vence_en > now` o `vence_en IS NULL`. Si el usuario no posee ninguno de los roles requeridos, eleva HTTP 403 Forbidden.
- **Razón**: Permite que la revocación de un rol surta efecto inmediatamente sobre una sesión abierta, sin esperar a que el token JWT expire.

### D2: Unificación de la Sesión de Base de Datos (Sección 6.7 del PDF)
- **Decisión**: Las dependencias de autenticación (`get_usuario_actual`), verificación de rol y los Unit of Work reciben la misma instancia de `AsyncSession` producida por `get_session`.
- **Razón**: Si la autenticación abriera su propia sesión y el Unit of Work abriera otra, cada petición autenticada tomaría dos conexiones simultáneas del pool de SQLAlchemy, agotándolo rápidamente.

### D3: Autoprotección del Administrador (`RN-05`)
- **Decisión**: Al revocar el rol `ADMIN` en `DELETE /usuarios/{id}/roles/ADMIN`:
  1. Si `usuario_actual.id == target_usuario_id`, se responde 409 Conflict ("Un administrador no puede revocarse su propio rol ADMIN").
  2. Se cuenta la cantidad de administradores vigentes en el sistema (`select count(*) where rol='ADMIN' and revocada_en is null`). Si es <= 1, se responde 409 Conflict ("El sistema no puede quedar sin administradores vigentes").
- **Razón**: Garantiza la operatividad continua del sistema de gestión.

### D4: Separación de Grupos de Rutas en `main.py` (`RN-06`)
- **Decisión**: FastAPI no permite restar dependencias en rutas hijas; solo sumarlas. Por tanto, en `main.py` se estructuran dos enrutadores:
  1. `api_abierta`: contiene `/health`, `/auth` y el catálogo público.
  2. `api_protegida`: monta como dependencia `dependencies=[Depends(verificar_cambio_password_obligatorio)]`. Si `usuario.debe_cambiar_password` es `True`, responde 403 Forbidden impidiendo el acceso a cualquier endpoint de negocio hasta que use `/auth/cambiar-password`.
- **Razón**: Resuelve el cambio obligatorio de contraseña montado una sola vez en la raíz del grupo protegido.

### D5: Validación de Timestamp de Vencimiento de Rol
- **Decisión**: En `AsignarRolRequest`, el campo `vence_en` valida mediante `@field_validator`:
  1. Debe tener zona horaria (`v.tzinfo is not None`). Si no tiene, lanza `ValueError("La fecha de vencimiento debe incluir zona horaria")` -> 422.
  2. Debe ser estrictamente futura (`v > datetime.now(timezone.utc)`). Si ya pasó, lanza `ValueError("La fecha de vencimiento debe estar en el futuro")` -> 422.
- **Razón**: Cumple estrictamente la regla de la página 11 del PDF ("una fecha sin zona es ambigua y una que ya pasó no choca con nada guardado; las dos son 422, no 409").

## Risks / Trade-offs

- **[Riesgo: Consulta adicional por cada request autenticado]** → *Mitigación*: La consulta de roles vigentes filtra por `(usuario_id, rol)` utilizando el índice único parcial `uq_asignacion_rol_abierta`, ejecutándose en milisegundos sin sobrecargar el motor.
