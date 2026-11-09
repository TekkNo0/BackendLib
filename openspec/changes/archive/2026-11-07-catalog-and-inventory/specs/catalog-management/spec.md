# Spec Delta

## Purpose

Permite gestionar el catálogo comercial de libros y entidades asociadas (editoriales, géneros, autores), asegurando reposición atómica e inmutabilidad de stock junto con borrado lógico y reuso de ISBN.

## ADDED Requirements

### Requirement: Alta de libro con autores y stock inicial
El sistema SHALL permitir a usuarios con rol ADMIN dar de alta nuevos libros especificando metadatos, lista de autores y un stock inicial no negativo, registrando el movimiento de stock correspondiente en una sola transacción.

#### Scenario: Alta exitosa con stock inicial positivo
- **WHEN** un usuario ADMIN envía `POST /libros` con ISBN válido, metadatos, `autores_ids` y `stock_inicial = 5`
- **THEN** el sistema responde HTTP 201 Created con los datos del libro, persiste las asociaciones de autor y registra un `MovimientoStock` de tipo 'ALTA' por 5 unidades en el mismo Unit of Work

#### Scenario: Alta rechazada por stock inicial negativo
- **WHEN** un usuario envía `POST /libros` con `stock_inicial < 0`
- **THEN** el sistema responde HTTP 422 Unprocessable Entity sin persistir ninguna entidad

### Requirement: Modificación de libro rechaza alteración de stock
El sistema SHALL permitir la modificación exclusiva de título y precio a través de `PATCH /libros/{id}`, y MUST rechazar con HTTP 422 cualquier solicitud que intente incluir el campo `stock` (RN-11).

#### Scenario: Modificación exitosa de título y precio
- **WHEN** un usuario ADMIN envía `PATCH /libros/{id}` con nuevos valores para `titulo` y `precio`
- **THEN** el sistema responde HTTP 200 OK con los datos actualizados y el stock permanece inalterado

#### Scenario: Intento de modificar stock devuelve 422
- **WHEN** un usuario envía `PATCH /libros/{id}` incluyendo el campo `stock` en el cuerpo de la petición
- **THEN** el sistema responde HTTP 422 Unprocessable Entity indicando que el stock sólo se altera mediante movimientos

### Requirement: Baja lógica y reutilización de ISBN
El sistema SHALL implementar borrado lógico mediante `DELETE /libros/{id}` estableciendo `borrado_en = now()`, ocultando el libro del catálogo comercial pero permitiendo reutilizar el mismo ISBN para un nuevo libro vigente (RN-13).

#### Scenario: Baja lógica responde 204 y oculta del catálogo
- **WHEN** un usuario ADMIN envía `DELETE /libros/{id}` para un libro vigente
- **THEN** el sistema actualiza `borrado_en` con la marca temporal actual, responde HTTP 204 No Content y el libro no vuelve a aparecer en `GET /libros`

#### Scenario: Reutilización de ISBN tras baja lógica responde 201
- **WHEN** se da de baja un libro con un ISBN específico y posteriormente se crea otro libro con el mismo ISBN
- **THEN** el sistema responde HTTP 201 Created permitiendo la creación gracias al índice único parcial

#### Scenario: Baja lógica de libro ya borrado responde 404
- **WHEN** se envía `DELETE /libros/{id}` para un libro cuyo `borrado_en` ya no es nulo
- **THEN** el sistema responde HTTP 404 Not Found

### Requirement: Reposición atómica de stock
El sistema SHALL proveer el endpoint `POST /libros/{id}/reponer` para incrementar el stock disponible registrando un `MovimientoStock` de tipo 'REPOSICION', rechazando reposiciones sobre libros dados de baja (RN-13).

#### Scenario: Reposición exitosa incrementa stock y crea movimiento
- **WHEN** un usuario ADMIN envía `POST /libros/{id}/reponer` con `cantidad = 10` y un motivo
- **THEN** el sistema responde HTTP 200 OK con el stock actualizado a `stock_anterior + 10` y genera una fila en `movimiento_stock`

#### Scenario: Reposición de libro borrado responde 409
- **WHEN** se envía `POST /libros/{id}/reponer` sobre un libro con `borrado_en IS NOT NULL`
- **THEN** el sistema responde HTTP 409 Conflict impidiendo la reposición sobre ítems descatalogados

### Requirement: Entidades accesorias del catálogo
El sistema SHALL proveer consulta pública para editoriales, géneros y autores, y restringir las operaciones de alta y modificación al rol ADMIN.

#### Scenario: Consulta pública de editoriales géneros y autores
- **WHEN** un usuario no autenticado solicita `GET /editoriales`, `GET /generos` o `GET /autores`
- **THEN** el sistema responde HTTP 200 OK con el listado paginado estándar de la entidad

#### Scenario: Creación y edición restringida a rol ADMIN
- **WHEN** un usuario sin rol ADMIN intenta crear o editar una editorial, género o autor
- **THEN** el sistema responde HTTP 403 Forbidden
