# Decisiones y Supuestos

## Decisiones documentadas

### DD-01 — Token en Cookie HttpOnly vs Cabecera Authorization
- **Decisión**: El token JWT se almacena exclusivamente en una cookie `access_token` con atributos `HttpOnly`, `SameSite=Lax` y `Max-Age`.
- **Contexto**: Los navegadores y clientes web deben mitigar el robo de sesiones mediante ataques de Cross-Site Scripting (XSS).
- **Alternativas consideradas**: Cabecera `Authorization: Bearer <token>` tradicional en memoria o local storage.
- **Justificación**: Con `HttpOnly`, scripts maliciosos no pueden leer el token. La cátedra exige expresamente rechazar peticiones con `Authorization: Bearer` en las rutas protegidas (Caso C-03).
- **Trade-offs**: Obliga al cliente HTTP a manejar cookies (o usar directivas `# @no-cookie-jar` en REST Client para pruebas multi-sesión).

### DD-02 — Autorización en Base de Datos vs Claims en JWT
- **Decisión**: Los roles del usuario se consultan contra la tabla `asignacion_rol` en PostgreSQL en cada solicitud protegida.
- **Contexto**: Si se revoca un rol a un usuario o este vence, el efecto debe ser inmediato, sin esperar a que el JWT expire (sección 5.9, RN-04).
- **Alternativas consideradas**: Autorizar confiando en el payload del JWT firmado.
- **Justificación**: Permite revocación en tiempo real (Caso C-07). Para optimizar el pool de conexiones, la dependencia comparte la misma sesión de base de datos que el Unit of Work (sección 6.7).
- **Trade-offs**: Requiere una consulta de base por petición protegida, mitigada por índices parciales rápidos.

### DD-03 — Invariante de Stock y Disparador de Sólo Agregado
- **Decisión**: El stock no se altera directamente con updates ad-hoc; se mantiene sincronizado mediante movimientos (`movimiento_stock`) con trigger que prohíbe `UPDATE` y `DELETE`.
- **Contexto**: Auditoría absoluta e inmutabilidad de movimientos de inventario (RN-11, RN-12).
- **Alternativas consideradas**: Triggers que re-calculen el stock o permisos de usuario de PostgreSQL a nivel de base.
- **Justificación**: Un trigger a nivel de base garantiza que ni siquiera un administrador o script manual de base de datos pueda adulterar o borrar movimientos de stock pasados.
- **Trade-offs**: Cualquier corrección requiere asentar un movimiento compensatorio.

### DD-04 — Registro de Intentos de Acceso en Transacción Independiente
- **Decisión**: Cada intento en `intento_acceso` se realiza en una sesión y transacción separada con commit inmediato.
- **Contexto**: Un intento fallido de login debe persistir aun cuando la transacción principal de la petición falle o se rechace (RN-07).
- **Alternativas consideradas**: Guardar en la misma sesión antes del error.
- **Justificación**: Si la sesión hace rollback por credenciales incorrectas, el registro del intento se perdería si no fuera independiente.
- **Trade-offs**: Incurre en una conexión breve adicional por login.

## Supuestos inferidos

### SU-01 — Entorno de Pruebas y Seed Determinístico
- **Supuesto**: Las pruebas automáticas y la corrección de la cátedra ejecutan `python seed.py` antes de cada suite `.http`.
- **Origen**: Consigna explícita del parcial ("Antes de cada archivo se corre python seed.py").
- **Riesgo si es falso**: Si las pruebas se corren secuencialmente sin reiniciar la base, los conteos de stock o rate limiting pueden desfasarse.
- **Cómo validar**: Diseñar `seed.py` de forma completamente idempotente y vaciar las tablas antes de cargar.

### SU-02 — Nombre del Grupo para la Entrega
- **Supuesto**: Se utiliza un nombre representativo provisional (ej. `Grupo_10`) para estructurar los zips y scripts de entrega, configurable por variable o argumento.
- **Origen**: Formato de entrega `Parcial_Cap1a6_<NombreDelGrupo>.zip`.
- **Cómo validar**: Consultar al usuario el nombre exacto de su grupo antes de generar el paquete final.
