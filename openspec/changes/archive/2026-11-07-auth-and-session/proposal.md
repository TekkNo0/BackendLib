# Proposal: Auth and Session

## Why
El parcial requiere un sistema de autenticación seguro basado en contraseñas cifradas con bcrypt y sesiones mantenidas exclusivamente mediante una cookie `HttpOnly` firmada con JWT (Ejercicio 4). Debe implementar protección contra ataques de temporización (RN-08), rate limiting en base de datos con respuesta 429 y cabecera `Retry-After` (RN-07), registro atómico de clientes en un solo Unit of Work (RN-02), auditoría en `evento_seguridad` (RN-16), y estricta validación de entrada con `extra="forbid"` y contraseñas de hasta 72 bytes.

## What Changes
- Definición de DTOs en `parcial/app/modules/usuarios/schemas.py`:
  - `extra="forbid"` en todos los contratos de entrada.
  - Validación de contraseña con límite estricto de 72 bytes UTF-8 (previene error 500 de bcrypt v5).
  - Respuestas sin `password_hash`. El login responde con `{mensaje, debe_cambiar_password, expira_en_segundos}` sin token en el cuerpo.
- Repositorios en `parcial/app/modules/usuarios/repository.py`:
  - `UsuarioRepository`: búsqueda por email, actualización de hash y bandera `debe_cambiar_password`.
  - `IntentoAccesoRepository`: conteo de intentos fallidos por ventana de tiempo (`contar_fallos_recientes`) y registro de intentos en sesión/transacción independiente que siempre confirma (Ejercicio 7).
  - `AsignacionRolRepository`: asignación y consulta de roles vigentes.
  - `EventoSeguridadRepository`: registro de eventos de auditoría (RN-16).
- Unit of Work en `parcial/app/modules/usuarios/unit_of_work.py`: compone repositorios de usuarios, roles, clientes y eventos de seguridad.
- Servicio de Autenticación en `parcial/app/modules/usuarios/service.py`:
  - Rate limiting previo al cálculo de hash: 5 fallos en 60s por (email, ip) devuelven 429 + `Retry-After` (RN-07).
  - Verificación en tiempo constante contra hash ficticio si el email no existe (RN-08).
  - Registro de clientes atómico (RN-02): usuario + rol CLIENTE + ficha de cliente en un solo bloque UoW. Conflicto responde 409 con mensaje propio.
  - Cambio de contraseña provisoria: actualiza contraseña, desactiva bandera y audita en `evento_seguridad` en la misma transacción (RN-16).
- Router de Autenticación en `parcial/app/modules/usuarios/router.py`:
  - Endpoints: `POST /auth/registro`, `POST /auth/login`, `POST /auth/logout`, `GET /auth/yo` y `POST /auth/cambiar-password`.
  - Login setea la cookie `access_token` (`HttpOnly=True`, `SameSite="lax"`, `Max-Age=1800`, `Secure=settings.COOKIE_SECURE`).
- Casos de prueba automatizados en `parcial/test/test_auth.py` y archivo `parcial/test/auth.http` (Casos C-02, C-03, C-04, C-05).

## Capabilities

### New Capabilities
- `user-authentication`: Autenticación con bcrypt fuera del loop, mitigación de timing attack mediante hash ficticio, rate limiting basado en tabla de intentos de acceso, cookie de sesión HttpOnly y registro atómico de clientes.

### Modified Capabilities
Ninguna.

## Impact
- Expone los endpoints de autenticación bajo el prefijo `/auth`.
- Sienta las bases para las dependencias de autorización de `C-05`.
