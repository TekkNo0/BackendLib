# Flujos Principales

## Flujo 1: Inicio de Sesión y Control de Tasa (Rate Limiting)

**Disparador**: Petición `POST /auth/login` recibida con `{ email, password }`.  
**Actor**: Cualquier usuario (Público o Registrado).

```
Cliente                 Router / Service            IntentoAcceso (Tx Propia)      Password Hash / BCrypt
  │                            │                               │                            │
  ├─── POST /auth/login ──────►│                               │                            │
  │                            ├─── 1. Check Rate Limit ──────►│ (SELECT COUNT(*) en 60s)   │
  │                            │    (>= 5 fallos? ──► 429)     │                            │
  │                            │                               │                            │
  │                            ├─── 2. Buscar Usuario ─────────┤                            │
  │                            │    (si no existe: dummy hash) │                            │
  │                            │                               │                            │
  │                            ├─── 3. Verificar Contraseña ───┼───────────────────────────►│ (bcrypt en thread)
  │                            │                               │                            │
  │                            ├─── 4. Anotar Intento ────────►│ (INSERT + COMMIT INMEDIATO)│
  │                            │                               │                            │
  │◄── Set-Cookie + 200/401 ───┴───────────────────────────────┴────────────────────────────┘
```

**Casos de error**:
- Formato inválido o password > 72 bytes → HTTP 422 sin tocar bcrypt.
- Rate limit excedido (5 fallos en 60s) → HTTP 429 con cabecera `Retry-After: 60`.
- Password incorrecta o usuario inexistente → HTTP 401 con mensaje genérico ("Credenciales incorrectas") en tiempo uniforme (RN-08).

---

## Flujo 2: Registro de una Venta Atómica

**Disparador**: Petición `POST /ventas` con `{ cliente_id, renglones: [{ libro_id, cantidad }] }`.  
**Actor**: Vendedor o Administrador autenticado.

```
Vendedor/Admin             Router                  VentasService              UnitOfWork / PostgreSQL
      │                      │                           │                              │
      ├─── POST /ventas ────►│                           │                              │
      │    (body json)       ├─── get_uow, user ────────►│                              │
      │                      │                           ├─── async with uow: ─────────►│ Inicia Transacción
      │                      │                           │                              │
      │                      │                           ├─── 1. Verificar cliente      │
      │                      │                           ├─── 2. Para c/ renglón:       │
      │                      │                           │       - Eager load libro     │
      │                      │                           │       - stock >= cant?       │
      │                      │                           │       - Descontar stock      │
      │                      │                           │       - Crear movimiento     │
      │                      │                           ├─── 3. Crear venta y renglones│
      │                      │                           │                              │
      │                      │                           ├─── (si falta stock) ────────►│ ROLLBACK (409)
      │                      │                           │                              │
      │                      │                           └─── Exitoso ─────────────────►│ COMMIT
      │                      │                                                          │
      │◄── 201 Created ──────┴── Encola BackgroundTask ─── (asyncio.sleep 0.5 + log) ───┘
```

**Casos de error**:
- Libro repetido en renglones → HTTP 422.
- Cliente inexistente o libro inexistente/dado de baja → HTTP 409.
- Stock insuficiente para algún ejemplar → HTTP 409, reversión completa de escrituras.

---

## Flujo 3: Autorización por Petición y Control de Roles

**Disparador**: Petición a cualquier ruta protegida (ej. `POST /libros` o `GET /mis-ventas`).  
**Actor**: Usuario con cookie `access_token`.

```
1. Dependencia `get_usuario_actual`:
   - Lee `access_token` de `request.cookies` (si falta → 401).
   - Valida firma y expiración del JWT (si falla → 401).
   - Busca el usuario en la BD (si no existe o está inactivo → 401).

2. Dependencia `control_cambio_obligatorio` (a nivel router protegido):
   - Si `usuario.debe_cambiar_password == True` → 403 Forbidden.

3. Dependencia `requiere_rol(roles)` (si el endpoint lo exige):
   - Consulta `asignacion_rol` en la base de datos para `usuario.id`.
   - Filtra filas con `revocada_en IS NULL` y `(vence_en IS NULL OR vence_en > now())`.
   - Si no posee al menos uno de los roles requeridos → 403 Forbidden.
```

---

## Flujo 4: Borrado Lógico y Reutilización de ISBN

**Disparador**: `DELETE /libros/{id}` seguido eventualmente de `POST /libros` con el mismo ISBN.

```
1. Baja Lógica:
   - Admin ejecuta DELETE /libros/{id}.
   - Se marca `borrado_en = now()` y se persiste. Retorna 204 No Content.
   - Las consultas de catálogo filtran `WHERE borrado_en IS NULL`.

2. Reutilización:
   - Admin ejecuta POST /libros con el mismo ISBN.
   - El índice único parcial `(isbn) WHERE borrado_en IS NULL` permite la inserción porque la fila anterior tiene `borrado_en IS NOT NULL`.
   - Se crea el nuevo libro activo con éxito (201).
   - Un segundo libro activo con el mismo ISBN colisiona contra el índice y devuelve 409.
```
