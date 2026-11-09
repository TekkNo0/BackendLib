# Tasks

## 1. DTOs y Validación de Roles

- [x] 1.1 Implementar esquemas en `parcial/app/modules/usuarios/schemas.py`: `AltaPersonalRequest`, `AsignarRolRequest` (con validación 422 para fecha sin timezone o pasada), `AsignacionRolResponse` y `EventoSeguridadResponse`.

## 2. Dependencias de Autorización y Grupos de Rutas

- [x] 2.1 Implementar `get_usuario_actual`, `requiere_rol` (consulta en BD en cada petición, RN-04) y `verificar_cambio_password_obligatorio` en `parcial/app/core/dependencies.py` compartiendo la sesión del request.
- [x] 2.2 Configurar `parcial/main.py` montando la verificación de cambio obligatorio de contraseña en el enrutador `api_protegida`.

## 3. Repositorios y Lógica de Administración

- [x] 3.1 Extender `AsignacionRolRepository` con métodos para contar administradores activos vigentes y revocar asignaciones abiertas.
- [x] 3.2 Implementar en `parcial/app/modules/usuarios/service.py`: `alta_personal`, `asignar_rol`, `revocar_rol` con autoprotección (RN-05), consulta de roles y listado paginado de eventos de auditoría (RN-16).

## 4. Router de Administración y Verificación

- [x] 4.1 Implementar `parcial/app/modules/usuarios/admin_router.py` con las rutas de personal, roles y eventos, montándolo en `api_protegida`.
- [x] 4.2 Implementar suite de pruebas en `parcial/test/test_authorization.py` y archivo `parcial/test/usuarios.http` validando casos C-06, C-07, C-08 y C-09.

## Workflow follow-up

- [x] Validar change con `openspec validate --strict`.
- [x] Archivar change con `openspec archive roles-and-admin-management -y`.
- [x] Actualizar `CHANGES.md`.
