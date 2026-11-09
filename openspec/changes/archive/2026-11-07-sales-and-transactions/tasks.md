# Tasks

## 1. DTOs y Validación de Ventas

- [x] 1.1 Implementar esquemas en `parcial/app/modules/ventas/schemas.py`: `RenglonVentaCreateRequest`, `VentaCreateRequest` (con validación de al menos un renglón y no repetición de libros, 422), `RenglonVentaResponse` y `VentaResponse` con precarga de cliente y libros.

## 2. Repositorio y Servicio Transaccional

- [x] 2.1 Implementar `VentaRepository` en `parcial/app/modules/ventas/repository.py` con precarga `selectinload` y métodos para listar ventas globales y por cliente.
- [x] 2.2 Implementar `VentaService` en `parcial/app/modules/ventas/service.py`: creación atómica en `UnitOfWork` (copia de precio, cálculo de total, descuento de stock, movimientos de salida y rollback ante stock insuficiente RN-10 / Caso C-15), consulta con aislamiento de cliente (RN-14 / Casos C-11 y C-12).

## 3. Router y Despacho Asincrónico

- [x] 3.1 Implementar `parcial/app/modules/ventas/router.py`: `POST /ventas` con encolamiento de `BackgroundTasks` (`asyncio.sleep(0.5)`), `GET /ventas`, `GET /ventas/{id}` y `GET /mis-ventas`.
- [x] 3.2 Montar el router de ventas en el grupo `api_protegida` en `parcial/main.py`.

## 4. Pruebas y Validación de Casos C-10, C-11, C-12 y C-15

- [x] 4.1 Implementar suite de pruebas en `parcial/test/test_sales.py` validando creación atómica, rollback por stock insuficiente (C-15), aislamiento de cliente y 403 en venta ajena (C-11, C-12).
- [x] 4.2 Crear archivo `parcial/test/ventas.http` con peticiones de prueba correspondientes a los casos C-10, C-11, C-12 y C-15.

## Workflow follow-up

- [x] Validar change con `openspec validate --strict`.
- [x] Archivar change con `openspec archive sales-and-transactions -y`.
- [x] Actualizar `CHANGES.md`.
