# Funcionalidades

Las historias de usuario están estructuradas por épica funcional para cubrir las consignas del parcial:

## Épica 1: Autenticación y Ciclo de Vida de Sesión
### US-001 — Registro de nuevos clientes
- **Como** visitante no registrado
- **Quiero** crear una cuenta con mi email, nombre y contraseña
- **Para** poder comprar y consultar mis pedidos por la web.
- **Criterios de aceptación**:
  - [ ] Crea `usuario`, `asignacion_rol` ('CLIENTE') y `cliente` en un único bloque transaccional atómico (RN-02).
  - [ ] Si el correo ya existe en `usuario` o `cliente`, devuelve 409 con mensaje de negocio.
  - [ ] Si la contraseña excede 72 bytes, devuelve 422 sin llegar a invocar bcrypt.
  - [ ] Retorna HTTP 201 Created sin exponer `password_hash`.

### US-002 — Inicio de sesión con cookie HttpOnly y Rate Limiting
- **Como** usuario registrado
- **Quiero** autenticarme con mis credenciales
- **Para** acceder a las funcionalidades del sistema según mis roles.
- **Criterios de aceptación**:
  - [ ] Emite el token JWT únicamente en la cabecera `Set-Cookie` (`access_token`, `HttpOnly`, `SameSite=Lax`, `Max-Age`). El cuerpo de la respuesta no contiene el token.
  - [ ] Si hay 5 fallos consecutivos para la misma tupla (email, ip) en los últimos 60 segundos, responde 429 con `Retry-After` sin calcular hash (RN-07).
  - [ ] Si las credenciales no son válidas o el usuario no existe, responde 401 en tiempo constante (RN-08).
  - [ ] Cada intento se asienta inmediatamente en `intento_acceso` en una sesión y transacción independiente confirmada.

### US-003 — Cierre de sesión y consulta de identidad
- **Como** usuario autenticado
- **Quiero** cerrar sesión o consultar mis datos
- **Para** finalizar mi actividad o verificar qué roles tengo activos.
- **Criterios de aceptación**:
  - [ ] `POST /auth/logout` limpia la cookie `access_token` estableciendo `Max-Age=0`.
  - [ ] `GET /auth/yo` devuelve los datos del usuario, roles vigentes en base y roles contenidos en el token.

### US-004 — Cambio obligatorio de contraseña
- **Como** usuario con contraseña provisoria
- **Quiero** actualizar mi contraseña
- **Para** desbloquear el acceso a las demás funcionalidades del sistema.
- **Criterios de aceptación**:
  - [ ] Si `debe_cambiar_password == True`, cualquier ruta fuera de `/auth` devuelve 403 (RN-06).
  - [ ] `POST /auth/cambiar-password` valida la contraseña anterior, actualiza el hash de la nueva y pone `debe_cambiar_password = False`.
  - [ ] Registra un evento en `evento_seguridad` en la misma transacción (RN-16).
  - [ ] La misma cookie de sesión sigue siendo válida inmediatamente después del cambio.

## Épica 2: Gestión de Personal, Roles y Auditoría
### US-005 — Alta de personal con clave provisoria
- **Como** administrador
- **Quiero** registrar a un nuevo empleado asignándole una clave inicial
- **Para** que pueda incorporarse al equipo de trabajo.
- **Criterios de aceptación**:
  - [ ] Requiere rol ADMIN (403 para otros roles, 401 si no hay sesión).
  - [ ] Crea el usuario con `debe_cambiar_password = True`.
  - [ ] Registra el evento en `evento_seguridad` con actor igual al usuario actual (RN-16).
  - [ ] Devuelve HTTP 201 Created.

### US-006 — Asignación y revocación de roles
- **Como** administrador
- **Quiero** otorgar o dar de baja roles a un usuario
- **Para** modular sus privilegios de acceso.
- **Criterios de aceptación**:
  - [ ] Asignación valida que la fecha de vencimiento (`vence_en`) tenga zona horaria y sea a futuro (422 si no cumple).
  - [ ] No permite más de una asignación abierta por rol (RN-03, responde 409).
  - [ ] Si se reasigna un rol previamente vencido, cierra la fila previa y abre una nueva.
  - [ ] Revocación escribe `revocada_en = now()` sin eliminar físicamente la fila.
  - [ ] Impide que un administrador revoque su propio rol ADMIN o que el sistema quede sin administradores vigentes (RN-05, responde 409).
  - [ ] Registra el evento en `evento_seguridad` dentro de la misma transacción (RN-16).

## Épica 3: Catálogo, Inventario y Borrado Lógico
### US-007 — Alta y modificación de libros
- **Como** administrador
- **Quiero** cargar un nuevo libro con su stock inicial o modificar sus datos básicos
- **Para** mantener actualizado el catálogo comercial.
- **Criterios de aceptación**:
  - [ ] `POST /libros` recibe `stock_inicial` y crea el libro junto a sus autores asociados y el `movimiento_stock` ("Stock inicial") en una sola transacción (RN-11).
  - [ ] `PATCH /libros/{id}` permite actualizar únicamente título y precio. Si se incluye el campo `stock`, responde 422 rechazándolo (RN-11).
  - [ ] El ISBN debe ser único entre los libros vigentes (`WHERE borrado_en IS NULL`).

### US-008 — Reposición de inventario
- **Como** administrador
- **Quiero** registrar la entrada de ejemplares para un libro existente
- **Para** reponer stock disponible para la venta.
- **Criterios de aceptación**:
  - [ ] `POST /libros/{id}/reponer` incrementa `libro.stock` y registra la entrada en `movimiento_stock` en un Unit of Work.
  - [ ] Si el libro está dado de baja lógicamente, responde 409 (RN-13).

### US-009 — Baja lógica y reuso de ISBN
- **Como** administrador
- **Quiero** descatalogar un libro sin borrar sus registros históricos
- **Para** que las ventas pasadas conserven la información del libro vendido.
- **Criterios de aceptación**:
  - [ ] `DELETE /libros/{id}` escribe `borrado_en = now()` y responde HTTP 204 No Content.
  - [ ] El libro deja de mostrarse en `GET /libros`.
  - [ ] Permite crear un nuevo libro con el mismo ISBN una vez dado de baja el anterior.
  - [ ] Intentar dar de baja un libro ya descatalogado responde 404.

## Épica 4: Ventas y Despacho Asincrónico
### US-010 — Registro atómico de ventas
- **Como** vendedor o administrador
- **Quiero** concretar una venta ingresando cliente y renglones con cantidades
- **Para** efectivizar la compra y descontar inventario en una única transacción.
- **Criterios de aceptación**:
  - [ ] No permite libros repetidos en la lista de renglones (422).
  - [ ] Copia precios del catálogo y calcula total en el backend (RN-09).
  - [ ] Verifica stock disponible; si alguno es insuficiente, hace rollback total y responde 409 (RN-10).
  - [ ] Crea venta, renglones, descuenta stock y registra un `movimiento_stock` por cada renglón.
  - [ ] Dispara comprobante simulado con `BackgroundTasks` (`asyncio.sleep(0.5)`) que loguea en consola únicamente tras el commit exitoso.

### US-011 — Consulta de ventas y detalle sin problema N+1
- **Como** usuario autenticado
- **Quiero** consultar ventas globales (si soy personal) o mis compras (si soy cliente)
- **Para** revisar facturación y comprobantes.
- **Criterios de aceptación**:
  - [ ] `GET /ventas/{id}` resuelve cliente, renglones y libros con precarga fija sin consultas N+1.
  - [ ] Un cliente sólo puede consultar ventas donde `venta.cliente_id == cliente.id` de su cuenta; ventas ajenas responden 403 (RN-14).
  - [ ] `GET /mis-ventas` lista paginada de las compras del cliente autenticado.
