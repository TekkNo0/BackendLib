# Tasks

## 1. DTOs y Contratos de Entrada/Salida

- [x] 1.1 Implementar `parcial/app/modules/usuarios/schemas.py` con `extra="forbid"`, validación de contraseña de máximo 72 bytes UTF-8 (HTTP 422), y esquemas para login, registro, respuesta de login y datos de `/auth/yo`.

## 2. Repositorios y Unit of Work de Usuarios

- [x] 2.1 Implementar repositorios en `parcial/app/modules/usuarios/repository.py` (`UsuarioRepository`, `IntentoAccesoRepository`, `AsignacionRolRepository`, `EventoSeguridadRepository`), incluyendo el registro de intento en sesión independiente con el comentario triple obligatorio.
- [x] 2.2 Implementar `UsuariosUnitOfWork` en `parcial/app/modules/usuarios/unit_of_work.py` componiendo los repositorios necesarios para transacciones atómicas.

## 3. Servicio y Router de Autenticación

- [x] 3.1 Implementar `parcial/app/modules/usuarios/service.py` con lógica de rate limiting previo (RN-07), timing attack con hash ficticio (RN-08), auto-registro atómico (RN-02) y cambio de contraseña con auditoría (RN-16).
- [x] 3.2 Implementar `parcial/app/modules/usuarios/router.py` exponiendo `POST /registro`, `POST /login`, `POST /logout`, `GET /yo`, y `POST /cambiar-password`, seteando la cookie `access_token` con HttpOnly.
- [x] 3.3 Montar el router de autenticación en `parcial/main.py` dentro de `api_abierta` con prefijo `/auth`.

## 4. Pruebas Automatizadas y Casos HTTP

- [x] 4.1 Implementar pruebas automatizadas en `parcial/test/test_auth.py` validando rate limit 429 con Retry-After, cookie HttpOnly, timing attack y validaciones 422.
- [x] 4.2 Crear `parcial/test/auth.http` con los casos de prueba C-02, C-03, C-04 y C-05 documentados con su resultado esperado.

## Workflow follow-up

- Validar change con `openspec validate --strict`.
- Archivar change con `openspec archive auth-and-session -y`.
- Actualizar `CHANGES.md`.
