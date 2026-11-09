# Design

## Context

El sistema cuenta con la persistencia base de `Venta`, `RenglonVenta`, `Cliente` y `MovimientoStock` (con disparador append-only en BD). Ver `proposal.md` para la motivación.

## Goals / Non-Goals

**Goals:**
- DTOs estrictos en Pydantic v2 que prohíban precios y totales del cliente y rechacen libros repetidos (422).
- Transaccionalidad atómica en `UnitOfWork` que garantice rollback total ante stock insuficiente (RN-10, Caso C-15).
- Despacho simulado desacoplado en segundo plano vía `BackgroundTasks` (`asyncio.sleep(0.5)`).
- Precarga exhaustiva `selectinload` para evitar el problema de N+1 en listados y detalle de ventas.
- Regla de aislamiento estricta: un cliente sólo accede a sus propias ventas; accesos ajenos responden HTTP 403 (RN-14, Casos C-11 y C-12).

**Non-Goals:**
- Integración real con pasarelas de pago o proveedores de correo electrónico.
- Generación de archivos PDF físicos (se simula el despacho por BackgroundTasks).

## Decisions

### Decisión 1: Precios y totales calculados exclusivamente en el servidor (RN-09)
- **Elección**: El contrato `RenglonVentaCreateRequest` sólo recibe `libro_id` y `cantidad`. `VentaCreateRequest` sólo recibe `cliente_id` y `renglones`. Los precios unitarios se leen del modelo `Libro` y el `total` se calcula sumando `precio_unitario * cantidad`.
- **Razón**: Previene cualquier manipulación o fraude en montos desde el cliente HTTP.

### Decisión 2: Detección temprana y rollback total ante stock insuficiente (RN-10, Caso C-15)
- **Elección**: Durante la iteración de renglones dentro de `async with self.uow:`, si cualquier libro tiene `libro.stock < item.cantidad`, se eleva de inmediato `HTTPException(status_code=409, detail=...)`.
- **Razón**: El manejador de contexto `UnitOfWork` ejecuta `session.rollback()`, asegurando que no se persista la venta, ni los renglones, ni ningún movimiento de stock, y que ningún libro sufra descuento parcial.

### Decisión 3: Generación de movimientos de stock negativos en el mismo UoW
- **Elección**: Por cada renglón de venta confirmado, se agrega un `MovimientoStock(libro_id=libro.id, venta_id=venta.id, usuario_id=usuario_id, cantidad=-item.cantidad, motivo=f"Venta #{venta.id}")`.
- **Razón**: Mantiene la invariante contable estricta: `libro.stock == SUM(movimiento_stock.cantidad)`.

### Decisión 4: Aislamiento por rol y cliente (RN-14)
- **Elección**: En `GET /ventas/{id}`, se evalúan los roles vigentes en base de datos. Si el usuario no tiene rol `'ADMIN'` ni `'VENDEDOR'`, se consulta su ficha en `Cliente` mediante `usuario_id`. Si `venta.cliente_id != cliente.id`, se responde HTTP 403 Forbidden.
- **Razón**: Garantiza privacidad y confidencialidad comercial entre clientes del sistema.

### Decisión 5: Precarga selectinload
- **Elección**: Toda consulta de ventas utiliza `selectinload(Venta.cliente)` y `selectinload(Venta.renglones).selectinload(RenglonVenta.libro)`.
- **Razón**: Resuelve el árbol relacional completo en dos o tres consultas optimizadas independientemente del número de renglones, evitando consultas N+1.

## Risks / Trade-offs

- **[Riesgo de condición de carrera en stock bajo alta concurrencia]**: Dos ventas concurrentes podrían leer el mismo stock.
  → *Mitigación*: La base de datos cuenta con `CheckConstraint("stock >= 0")` que rechazaría a nivel motor cualquier saldo negativo, complementado por la validación del servicio.
