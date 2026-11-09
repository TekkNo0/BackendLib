# Proposal

## Why

El negocio de la librería necesita registrar transacciones de venta de forma atómica y consistente, garantizando que el stock se descuente con exactitud y se preserve la inmutabilidad de movimientos (RN-09, RN-10). Es crítico que los clientes no puedan fijar precios ni totales, que un stock insuficiente aborte la transacción completa con reversión inmediata (RN-10, Caso C-15), que el comprobante se despache de manera asincrónica tras la confirmación exitosa, y que los clientes autenticados accedan exclusivamente a sus propias ventas (RN-14, Casos C-11 y C-12).

## What Changes

- Endpoints de ventas en `parcial/app/modules/ventas/router.py`:
  - `POST /ventas`: creación de venta atómica restringida a `ADMIN` y `VENDEDOR`. Recibe `cliente_id` y `renglones` (mínimo 1, libros no repetidos). Copia los precios vigentes del catálogo, calcula el total en el servidor (RN-09), descuenta el stock de cada libro, registra los movimientos de stock tipo salida y dispara el despacho en segundo plano (`BackgroundTasks`, `asyncio.sleep(0.5)`).
  - Rechazo con HTTP 409 Conflict y rollback total ante stock insuficiente para cualquiera de los libros solicitados (Caso C-15).
  - `GET /ventas`: listado paginado de ventas para personal (`ADMIN` y `VENDEDOR`) con precarga fija sin consultas N+1 (`selectinload`).
  - `GET /ventas/{id}`: detalle de venta con sus renglones y libros. Aislamiento por cliente: si quien consulta es un `CLIENTE`, sólo puede ver ventas asociadas a su `cliente_id`, respondiendo HTTP 403 si intenta acceder a una venta ajena (RN-14, Casos C-11 y C-12).
  - `GET /mis-ventas`: listado paginado de compras del cliente autenticado.
- DTOs y validaciones Pydantic v2 en `parcial/app/modules/ventas/schemas.py`.
- Repositorio y Servicio de ventas con transaccionalidad mediante `UnitOfWork`.
- Casos de prueba automatizados en `parcial/test/test_sales.py` y archivo `parcial/test/ventas.http`.

## Capabilities

### New Capabilities
- `sales-transactions`: Circuito transaccional de ventas con cálculo de total en servidor, validación y rollback por stock insuficiente, despacho asincrónico y aislamiento de clientes.

### Modified Capabilities
<!-- None -->

## Impact

- Nuevos esquemas en `parcial/app/modules/ventas/schemas.py`.
- Repositorio `VentaRepository` en `parcial/app/modules/ventas/repository.py`.
- Servicio `VentaService` en `parcial/app/modules/ventas/service.py`.
- Router `ventas/router.py` montado en `api_protegida` en `parcial/main.py`.
- Tests unitarios y de integración para Casos C-10, C-11, C-12 y C-15.
