# Proposal

## Why

El sistema de librería requiere la gestión del catálogo comercial (libros, editoriales, géneros, autores) y la trazabilidad inmutable de su inventario. Es indispensable garantizar que el stock de los libros únicamente se modifique mediante movimientos tipificados en `movimiento_stock` (RN-11), que el borrado de libros sea puramente lógico preservando el historial para ventas pasadas pero permitiendo el reuso del ISBN para nuevas altas vigentes (RN-13), y que se expongan endpoints públicos de lectura y endpoints administrativos restringidos por RBAC.

## What Changes

- Endpoints CRUD para entidades accesorias (`editoriales`, `generos`, `autores`):
  - Lectura pública paginada: `GET /editoriales`, `GET /generos`, `GET /autores`, y `GET /{entidad}/{id}/libros`.
  - Creación y edición protegida para rol `ADMIN`: `POST` y `PATCH` para editoriales, géneros y autores.
- Endpoints del Catálogo Comercial de Libros:
  - `GET /libros`: listado público paginado estándar (`items`, `total`, `page`, `size`, `pages`) filtrando libros vigentes (`borrado_en IS NULL`) con filtro insensible a mayúsculas por `titulo`.
  - `GET /libros/{id}`: detalle público del libro vigente con autores, género y editorial.
  - `POST /libros`: alta protegida (`ADMIN`) de libro con autores asociados (`LibroAutor`) y stock inicial mediante registro en `movimiento_stock` tipo `'ALTA'`.
  - `PATCH /libros/{id}`: modificación de `titulo` y `precio` únicamente. Rechazo estricto con HTTP 422 si la petición contiene el campo `stock` (RN-11).
  - `DELETE /libros/{id}`: baja lógica escribiendo `borrado_en = now()` con respuesta HTTP 204 No Content. La unicidad parcial de ISBN permite dar de alta un nuevo libro con el mismo ISBN tras la baja (RN-13). Intentar borrar un libro ya descatalogado responde 404.
  - `POST /libros/{id}/reponer`: reposición de inventario protegida (`ADMIN`) que incrementa `libro.stock` y registra la entrada en `movimiento_stock` tipo `'REPOSICION'` en el mismo UoW. Si el libro está dado de baja lógicamente, responde 409 (RN-13).
  - `GET /libros/{id}/movimientos`: listado paginado del historial de movimientos de stock del libro (restringido a `ADMIN`).
- Casos de prueba automatizados y archivos HTTP para verificación de casos C-13 y C-16.

## Capabilities

### New Capabilities
- `catalog-management`: Gestión de catálogo comercial, relaciones editorial/género/autor, borrado lógico con reuso de ISBN y reposición atómica de stock.

### Modified Capabilities
<!-- None -->

## Impact

- Nuevos esquemas y DTOs Pydantic v2 en `parcial/app/modules/libros/schemas.py`, `parcial/app/modules/editoriales/schemas.py`, `parcial/app/modules/generos/schemas.py`, `parcial/app/modules/autores/schemas.py`.
- Repositorios y routers para `editoriales`, `generos`, `autores` y `libros`.
- Inclusión de routers en `parcial/main.py` respetando la separación entre `api_abierta` y `api_protegida`.
- Suite de pruebas en `parcial/test/test_catalog.py` y `parcial/test/libros.http` (casos C-13 y C-16).
