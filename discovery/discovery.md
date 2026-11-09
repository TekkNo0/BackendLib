# Discovery — Parcial: La librería con acceso, transacciones y despliegue en el VPS

**Fecha**: 2026-11-03  
**Fuentes investigadas**: Consigna oficial de la cátedra UTN - Programación III (`docs/consigna_parcial.md`)

---

## 1. Problema que resuelve

Evolucionar el sistema de gestión de catálogo, clientes y ventas de la librería (capítulos 1 a 4) incorporando autenticación robusta mediante cookies `HttpOnly`, autorización granular por roles vigentes consultados en la base de datos (ADMIN, VENDEDOR, CLIENTE), integridad de stock garantizada exclusivamente mediante tabla de sólo agregado con disparador PostgreSQL, y transaccionalidad atómica vía Unit of Work y Repositorios sin filtración de errores internos; sumado al despliegue contenedorizado en VPS bajo imagen minimalista Alpine.

---

## 2. Usuarios / roles

- **ADMIN**: Administrador del sistema. Mantiene el catálogo de libros, repone stock, administra personal, asigna y revoca roles con vigencia, y consulta eventos de auditoría/seguridad.
- **VENDEDOR**: Personal de atención. Atiende clientes en mostrador, registra clientes y ventas atómicas con descuento de stock y cálculo de totales en servidor.
- **CLIENTE**: Usuario final de la librería. Se auto-registra (creando usuario, rol CLIENTE y cliente en un solo Unit of Work), consulta catálogo público y visualiza exclusivamente sus propias compras (`/mis-ventas`).
- **PÚBLICO / ANÓNIMO**: Visitante sin sesión que puede explorar el catálogo de libros, editoriales y autores sin autenticarse.

---

## 3. Casos de uso

1. **Auto-registro de Cliente**: Como visitante, quiero registrarme ingresando email, nombre y contraseña para obtener una cuenta de cliente y rol CLIENTE de forma atómica.
2. **Autenticación con Cookie Segura y Rate Limiting**: Como usuario, quiero iniciar sesión recibiendo una cookie `access_token` HttpOnly, con bloqueo temporal (429) tras 5 intentos fallidos en 60 segundos por IP/email.
3. **Registro Atómico de Venta y Descuento de Stock**: Como vendedor, quiero registrar una venta con múltiples renglones donde el servidor verifique y descuente el stock, calcule totales y emita comprobante simulado en segundo plano, revirtiendo todo si un libro no alcanza.
4. **Borrado Lógico y Reutilización de ISBN**: Como administrador, quiero dar de baja un libro sin borrarlo físicamente para preservar ventas históricas, permitiendo reutilizar su ISBN para un nuevo ejemplar activo.
5. **Consulta de Ventas Propias**: Como cliente, quiero ver el detalle de mis compras pasadas con sus renglones y libros, sin poder acceder a ventas de otros clientes.

---

## 4. Competidores / soluciones existentes

| Solución / Referencia | Enfoque | Limitaciones observadas en TP Cap 1-4 | Diferenciador del Parcial |
|---|---|---|---|
| TP Capítulos 1 a 4 (Base) | API FastAPI con endpoints directos y SQLAlchemy plano | Sin control de acceso ni roles; stock editable por PATCH sin trazabilidad; transacciones dispersas; sin borrado lógico de ISBN. | Arquitectura estricta Router → Service → UoW → Repository → Model; RBAC en base por petición; stock inmutable vía trigger de sólo agregado. |
| Sistemas monolíticos tradicionales | Autenticación con sesión en memoria / tokens en header | Dificultad para revocar accesos en tiempo real y vulnerabilidad a filtración de tokens en frontend. | Token en cookie `HttpOnly`, validación de vigencia de roles en Postgres en cada request, bcrypt fuera del bucle con semáforo. |

---

## 5. Funcionalidades necesarias (Innegociables para el Parcial)

- **Arquitectura en capas formal**: Router → Service → Unit of Work → Repository → Model en todos los módulos.
- **Autenticación y Seguridad**: Hashing con bcrypt fuera del event loop (`to_thread` con semáforo), max 72 bytes; token JWT en cookie `access_token` (`HttpOnly`, `SameSite=Lax`); login dummy para tiempo constante; registro atómico (RN-02); cambio forzado de contraseña en rutas protegidas (RN-06).
- **Control de Acceso y Roles**: `asignacion_rol` con vigencia (`desde`, `vence_en`, `revocada_en`); consulta a base en cada petición; protección contra auto-revocación del último ADMIN (RN-05).
- **Gestión de Stock y Movimientos**: `movimiento_stock` como única vía de alteración de stock (alta, reposición, ventas); disparador en PostgreSQL que rechaza UPDATE y DELETE (RN-12).
- **Venta Atómica**: Creación de venta, renglones, actualización de stock y movimientos en un solo Unit of Work; simulación de comprobante con `BackgroundTasks`.
- **Borrado Lógico**: Campo `borrado_en` en `libro`; índice único parcial `(isbn) WHERE borrado_en IS NULL`.
- **Paginación Uniforme**: Envoltorio `{items, total, page, size, pages}` con validación estricta de páginas.
- **Migraciones Alembic**: Migración autogenerada para nuevas tablas y migración manual para trigger de sólo agregado.
- **Pruebas y Scripts**: Suite de tests `.http` (C-01 a C-16), script SQL (`solo_agregado.sql`) y `seed.py` determinístico.
- **Empaquetado y Despliegue**: Dockerfile basado en `python:3.12-alpine` (< 100 MB base), usuario no-root, variables por `.env-file`, sin credenciales quemadas.

---

## 6. Funcionalidades opcionales (Fuera de alcance)

- Concurrencia pesada y bloqueo pesimista contra actualizaciones perdidas (reservado para Capítulo 7).
- Colas de tareas distribuidas con Celery o Redis (reservado para Capítulo 8); el envío de comprobantes se simula en el mismo proceso con `BackgroundTasks` y `asyncio.sleep(0.5)`.

---

## 7. Reglas de negocio críticas

- **RN-01 a RN-03**: Unicidades garantizadas por BD con respuestas 409 legibles sin exponer el esquema. Asignación única abierta por rol.
- **RN-04**: Autorización resuelta en cada petición consultando `asignacion_rol` en la base de datos (el token JWT no autoriza por sí solo).
- **RN-05**: El administrador no puede revocar su propio rol ADMIN y el sistema nunca puede quedar sin administradores vigentes.
- **RN-07**: Rate-limiting de 5 fallos en 60s por (email, ip) devolviendo 429 con `Retry-After`. Los intentos se registran en `intento_acceso` en su propia sesión/transacción inmediata que sobrevive al rollback.
- **RN-10 & RN-11**: Stock atómico e inmutable por PATCH; venta descuenta stock y registra movimientos en una sola transacción.
- **RN-12**: `movimiento_stock` es estrictamente append-only mediante trigger de base de datos.
- **RN-15**: Ningún error expone detalles de base de datos o trazas (sin 500 por datos inválidos).
- **RN-16**: Auditoría en `evento_seguridad` para altas de personal, cambios de rol y cambios de contraseña en la misma transacción del cambio.

---

## 8. Integraciones

- **PostgreSQL 16**: Motor relacional primario mediante driver `asyncpg` y SQLAlchemy 2.0 async.
- **Docker / VPS**: Servidor Linux con PostgreSQL existente donde corre el contenedor del TP de los capítulos 1 a 4.

---

## 9. Restricciones técnicas y académicas

- Stack obligatorio: Python 3.12, FastAPI 0.111+, SQLModel 0.0.24, SQLAlchemy 2.0+, Alembic 1.13+, asyncpg 0.30+, pydantic-settings 2.0+.
- No utilizar `create_all`; esquema creado exclusivamente por migraciones de Alembic.
- Cero contraseñas o firmas JWT por defecto en el código o repositorio.
- Estructura de entrega exacta: Zip conteniendo carpetas `parcial/` y `despliegue/`.

---

## 10. Riesgos

- **Bloqueo del event loop de FastAPI**: Si bcrypt se ejecuta sincrónicamente en el event loop. *Mitigación: `asyncio.to_thread` con semáforo de concurrencia*.
- **Inconsistencia de stock y movimientos**: Si alguna ruta modifica `libro.stock` sin crear un `movimiento_stock`. *Mitigación: Un solo punto de servicio para alteración de stock*.
- **Fuga de credenciales o secretos**: Subir archivos `.env` o credenciales reales al repositorio o a la imagen Docker. *Mitigación: `.gitignore` y `.dockerignore` estrictos, variables vía `--env-file`*.
- **Fallas de conexión en Docker Alpine**: Problemas de resolución localhost en Alpine para el HEALTHCHECK. *Mitigación: Utilizar `127.0.0.1:8000/health/live` con `wget`*.

---

## 11. Preguntas abiertas

- Nombre del grupo para el empaquetado final (`Parcial_Cap1a6_<NombreDelGrupo>.zip`).
- Acceso real al VPS o preparación integral de la evidencia simulada (archivos `DEPLOY.md`, `evidencia/` con logs de docker y psql).
