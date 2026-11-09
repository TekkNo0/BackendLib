# Visión y Objetivos

## Propósito del sistema
Evolucionar la API asincrónica de la librería (construida en los capítulos 1 a 4) incorporando una arquitectura en capas formal (Router → Service → Unit of Work → Repository → Model), autenticación robusta mediante cookies HttpOnly, autorización consultando roles vigentes en base de datos en cada petición, y una gestión transaccional estricta donde el stock se altera exclusivamente mediante movimientos de sólo agregado protegidos por un disparador en PostgreSQL. Adicionalmente, empaquetar el TP base en un contenedor Docker minimalista para su puesta en producción en un VPS.

## Objetivos por actor

| Actor | Objetivo principal | Objetivos secundarios |
|---|---|---|
| **ADMIN** | Mantener catálogo, reponer inventario y gobernar accesos y roles del personal | Auditar eventos de seguridad, dar de baja libros lógicamente, supervisar movimientos de stock |
| **VENDEDOR** | Registrar ventas atómicas de mostrador y gestionar clientes | Consultar ventas globales, asegurar que ninguna venta se registre sin stock |
| **CLIENTE** | Auto-registrarse de forma autónoma y consultar su historial de compras | Acceder a su perfil, explorar el catálogo público |
| **PÚBLICO** | Consultar el catálogo de libros, autores y editoriales | Explorar disponibilidad y precios sin necesidad de credenciales |

## Alcance (Parcial: Capítulos 1 a 6)
- **Reorganización en capas limpias**: Router → Service → UoW → Repository → Model. Ningún servicio recibe la sesión; ningún repositorio ejecuta `commit()`.
- **Evolución del esquema con Alembic**: Migración autogenerada para nuevas entidades y migración manual para el trigger de sólo agregado.
- **Autenticación segura**: Hash con `bcrypt` (fuera del bucle de eventos, con semáforo y límite estricto de 72 bytes) y emisión de JWT en cookie `HttpOnly` (`SameSite=Lax`). Rate limiting en memoria/base de 5 intentos fallidos en 60 segundos con respuesta 429 (`Retry-After`).
- **Autorización por base en tiempo real**: Tabla `asignacion_rol` con vigencia (`desde`, `vence_en`, `revocada_en`); resolución de permisos en base en cada petición y distinción tajante entre 401 y 403.
- **Transaccionalidad y Unit of Work**: Agrupamiento de escrituras en una sola transacción atómica (auto-registro, ventas, cambio de roles y auditoría).
- **Invariante de Stock y Sólo Agregado**: El stock de cada libro equivale exactamente a la suma de sus movimientos. `movimiento_stock` protegido contra `UPDATE` y `DELETE` por trigger.
- **Borrado Lógico y Reutilización de ISBN**: Libros con `borrado_en` e índice único parcial `(isbn) WHERE borrado_en IS NULL`.
- **Paginación Uniforme**: Envoltorio `{items, total, page, size, pages}` con validación estricta (página inexistente responde 422).
- **Despliegue Contenedorizado**: Empaquetado del TP capítulos 1 a 4 con Dockerfile basado en `python:3.12-alpine` (< 100 MB base), usuario sin privilegios, migraciones automáticas al inicio y healthcheck en IPv4.

## Fuera de alcance
- Concurrencia de reservas simultáneas y niveles de aislamiento pesimistas (tema del Capítulo 7).
- Colas de tareas distribuidas con Redis (tema del Capítulo 8); el envío de comprobantes se simula asincrónicamente mediante `BackgroundTasks` en el mismo proceso.
- Interfaz gráfica frontend (el entregable consiste en la API REST, scripts de verificación y suite de pruebas `.http`).
