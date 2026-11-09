# Design: Auth and Session

## Context
El parcial requiere un sistema de autenticación seguro basado en contraseñas cifradas con `bcrypt` y sesiones transportadas en cookies `HttpOnly` firmadas con JWT (Ejercicio 4). Las operaciones de autenticación deben prevenir ataques de temporización (RN-08), denegación de servicio por fuerza bruta mediante rate limiting (RN-07), y garantizar atomicidad en el auto-registro (RN-02) y auditoría (RN-16).

## Goals / Non-Goals

**Goals:**
- DTOs separados de los modelos de tabla con `extra="forbid"` y validación de hasta 72 bytes en contraseñas.
- Flujo de login en 3 pasos: 1) rate limit en `intento_acceso` (devuelve 429 + `Retry-After`), 2) verificación de contraseña (contra usuario o hash ficticio), 3) registro de intento en sesión independiente.
- Registro de `intento_acceso` con sesión y transacción independientes que siempre hacen commit.
- Entrega de token JWT exclusivamente en la cookie `access_token` con directivas `HttpOnly`, `SameSite=Lax`, `Max-Age` y `Secure` configurable.
- Endpoints: `POST /auth/registro`, `POST /auth/login`, `POST /auth/logout`, `GET /auth/yo` y `POST /auth/cambiar-password`.

**Non-Goals:**
- Control de roles (`requiere_rol`) y endpoints administrativos de asignación/revocación de roles — asignados a C-05.
- Filtro de rutas abiertas vs protegidas para usuarios con cambio de contraseña obligatorio — asignado a C-05.

## Decisions

### D1: Orden de Evaluación en Login (RN-07 y RN-08)
- **Decisión**: El login sigue estrictamente este orden:
  1. Consulta en `intento_acceso` la cantidad de intentos fallidos para el par `(email, ip)` en los últimos 60 segundos posteriores al último login exitoso. Si es >= 5, responde 429 con cabecera `Retry-After: 60` inmediatamente, **sin calcular ningún hash**.
  2. Si no superó el límite, busca el usuario por email. Si el usuario no existe, ejecuta `verify_password` contra el `app.state.dummy_hash`. Si existe, ejecuta `verify_password` contra su `password_hash`.
  3. Si la verificación falla (o el usuario no existía), registra el intento fallido en `intento_acceso` y responde 401 `{"detail": "Credenciales incorrectas"}`.
  4. Si la verificación es correcta, registra el intento exitoso en `intento_acceso`, reseteando el conteo de fallos para futuros intentos.
- **Razón**: El cálculo de bcrypt toma ~300ms. Ejecutar el rate limit primero protege al servidor de DoS por CPU. Ejecutar el dummy hash garantiza tiempo constante si el usuario no existe, mitigando ataques de enumeración (timing attacks).

### D2: Registro de Intento de Acceso en Sesión Independiente (Ejercicio 7 / Sección 6.8.1)
- **Decisión**: Para anotar en `intento_acceso`, se utiliza una función que abre una nueva sesión asincrónica desde `request.app.state.session_factory`, ejecuta el insert y hace `commit()` inmediatamente en un bloque propio.
- **Razón y Comentario Obligatorio**:
  - *Qué hace distinto*: No usa la sesión de la petición, sino una sesión y transacción propias.
  - *Por qué no puede compartir la transacción*: Porque el fallo de login revierte la transacción de la petición (rollback), y el intento fallido debe persistirse para que el contador de rate limiting funcione.
  - *Cuál es su costo*: Deja filas grabadas en la base de datos aun cuando la petición falle o sea rechazada.

### D3: Cookie HttpOnly y Cuerpo de Login
- **Decisión**: `POST /auth/login` devuelve `{ "mensaje": "Sesión iniciada", "debe_cambiar_password": bool, "expira_en_segundos": 1800 }`. El token JWT viaja únicamente en el encabezado `Set-Cookie: access_token=...; HttpOnly; SameSite=Lax; Path=/; Max-Age=1800`.
- **Razón**: Cumple el requisito explícito de Ejercicio 4 ("el cuerpo del login no lo trae, viaja sólo en una cookie access_token con HttpOnly").

### D4: Auto-registro Atómico (RN-02)
- **Decisión**: `POST /auth/registro` abre un único bloque `UnitOfWork`. En ese bloque crea: 1) `Usuario`, 2) `AsignacionRol` con `rol='CLIENTE'`, 3) `Cliente`. Si el email ya existe en `usuario` o en `cliente`, lanza 409 con mensaje propio y la transacción revierte por completo.
- **Razón**: Garantiza que no queden usuarios sin cliente ni clientes sin rol (o quedan las 3 filas, o ninguna).

## Risks / Trade-offs

- **[Riesgo: Excepciones de 500 por contraseñas > 72 bytes en bcrypt v5]** → *Mitigación*: Validación en DTO de entrada con `@field_validator("password")` que comprueba `len(v.encode('utf-8')) <= 72`, devolviendo 422 si se supera.
- **[Riesgo: Ataque de enumeración por diferencia de mensajes de error]** → *Mitigación*: Tanto usuario inexistente como contraseña errónea devuelven el mismo código 401 y el mismo mensaje `Credenciales incorrectas`.
