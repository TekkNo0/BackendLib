# Proposal: Roles and Admin Management

## Why
El parcial requiere un esquema de autorización granular basado en roles vigentes consultados en la base de datos en cada petición HTTP (RN-04), autoprotección de administradores (RN-05), segregación de rutas abiertas y protegidas para cambio obligatorio de contraseña (RN-06), gestión de personal con contraseñas provisorias y auditoría transaccional en `evento_seguridad` (RN-16).

## What Changes
- Dependencias de autenticación y autorización en `parcial/app/core/dependencies.py`:
  - `get_usuario_actual`: valida cookie, token, y obtiene el usuario activo desde la base de datos en la misma sesión del request (401 si no hay cookie, expiró o está inactivo).
  - `requiere_rol(*roles)`: consulta roles vigentes en `asignacion_rol` en la base de datos en cada petición (RN-04) y responde 403 Forbidden si no posee el rol necesario.
  - `control_cambio_password_obligatorio`: si `usuario.debe_cambiar_password == True`, responde 403 impidiendo el acceso a rutas protegidas (RN-06).
- Montaje de dos grupos de rutas en `parcial/main.py`:
  - `api_abierta`: no exige sesión (salud, catálogo público, login, registro, logout).
  - `api_protegida`: monta como dependencia global única `dependencies=[Depends(control_cambio_password_obligatorio)]` (RN-06).
- DTOs en `parcial/app/modules/usuarios/schemas.py`:
  - `AltaPersonalRequest`: nombre, email, password provisoria (máx 72 bytes). `extra="forbid"`.
  - `AsignarRolRequest`: rol (ADMIN, VENDEDOR, CLIENTE), vence_en opcional (validado con timezone y en el futuro, 422 si ya pasó o no tiene zona). `extra="forbid"`.
  - `AsignacionRolResponse`: id, rol, desde, vence_en, revocada_en, otorgada_por.
  - `EventoSeguridadResponse`: id, cuando, actor, accion.
- Servicios y métodos en `parcial/app/modules/usuarios/service.py`:
  - `alta_personal`: crea usuario con `debe_cambiar_password = True` y registra evento en `evento_seguridad` en la misma transacción (RN-16). Solo ADMIN. 201 Created.
  - `get_roles`: lista historial de roles de un usuario. Solo ADMIN. 200 OK.
  - `asignar_rol`: valida fecha futura con timezone (422), verifica unicidad de rol abierto (RN-03); si ya existía un rol revocado o vencido, cierra anterior y abre nuevo. Audita en `evento_seguridad` (RN-16).
  - `revocar_rol`: establece `revocada_en = now()`. Valida autoprotección (RN-05: no revocar el propio ADMIN con 409 y no dejar el sistema con 0 ADMINs vigentes con 409). Audita en `evento_seguridad`.
  - `listar_eventos`: paginado estándar `{items, total, page, size, pages}`. Solo ADMIN.
- Router de administración en `parcial/app/modules/usuarios/admin_router.py`:
  - `POST /usuarios`, `GET /usuarios/{id}/roles`, `POST /usuarios/{id}/roles`, `DELETE /usuarios/{id}/roles/{rol}`, `GET /eventos`.
- Tests unitarios y de integración en `parcial/test/test_authorization.py` y archivo `parcial/test/usuarios.http` (Casos C-06, C-07, C-08, C-09).

## Capabilities

### New Capabilities
- `user-authorization`: Autorización con roles vigentes consultados en base de datos en cada petición, autoprotección de administradores, asignación y revocación con vigencia e histórico, y bloqueo de usuarios con cambio obligatorio de contraseña montado en grupo protegido.

### Modified Capabilities
Ninguna.

## Impact
- Establece el control de acceso en capas y las rutas de administración del personal y roles.
