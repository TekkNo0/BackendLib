# Tasks

## 1. DTOs y Esquemas de Catálogo

- [x] 1.1 Implementar esquemas Pydantic v2 en `parcial/app/modules/libros/schemas.py`: `LibroCreateRequest`, `LibroUpdateRequest` (con validación 422 para `stock`), `LibroResponse`, `LibroDetalleResponse`, `ReponerStockRequest` y `MovimientoStockResponse`.
- [x] 1.2 Implementar esquemas en `parcial/app/modules/editoriales/schemas.py`, `parcial/app/modules/generos/schemas.py` y `parcial/app/modules/autores/schemas.py`.

## 2. Repositorios y Servicios de Catálogo

- [x] 2.1 Implementar repositorios para libros, movimientos de stock, editoriales, géneros y autores (`LibroRepository`, `MovimientoStockRepository`, etc.) con soporte de paginación y precarga `selectinload`.
- [x] 2.2 Implementar `LibroService` con alta atómica y stock inicial, modificación sin stock, baja lógica (`DELETE`), reposición y listados con filtro por título insensible a mayúsculas.

## 3. Routers y Registro en Aplicación

- [x] 3.1 Implementar routers públicos y protegidos en `parcial/app/modules/libros/router.py`, `parcial/app/modules/editoriales/router.py`, `parcial/app/modules/generos/router.py` y `parcial/app/modules/autores/router.py`.
- [x] 3.2 Montar las rutas públicas en `api_abierta` y las rutas administrativas en `api_protegida` en `parcial/main.py`.

## 4. Pruebas y Validación de Casos C-13 y C-16

- [x] 4.1 Implementar suite de pruebas en `parcial/test/test_catalog.py` validando alta con autores, rechazo de `stock` en PATCH (422, C-13), baja lógica (204) y reuso de ISBN (201, C-16).
- [x] 4.2 Crear archivo `parcial/test/libros.http` con peticiones de prueba para C-13 y C-16.

## Workflow follow-up

- [x] Validar change con `openspec validate --strict`.
- [x] Archivar change con `openspec archive catalog-and-inventory -y`.
- [x] Actualizar `CHANGES.md`.
