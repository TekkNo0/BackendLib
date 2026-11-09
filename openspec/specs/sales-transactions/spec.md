# sales-transactions Specification

## Purpose
Permite gestionar el circuito comercial de ventas con cálculo de totales en servidor, descuento atómico de inventario, despacho asincrónico y aislamiento estricto de datos por cliente.

## Requirements

### Requirement: Registro atómico de ventas con cálculo en servidor
El sistema SHALL permitir a usuarios con rol ADMIN o VENDEDOR registrar ventas de forma atómica, validando que contenga al menos un renglón sin libros duplicados, copiando los precios vigentes del catálogo y calculando el total en el servidor (RN-09).

#### Scenario: Venta exitosa calcula total y copia precios
- **WHEN** un vendedor envía `POST /ventas` con un `cliente_id` válido y renglones con cantidades positivas sin enviar precio ni total
- **THEN** el sistema responde HTTP 201 Created con el total calculado y los precios unitarios vigentes copiados en cada renglón

#### Scenario: Venta rechazada por renglones con libros duplicados
- **WHEN** se envía `POST /ventas` con el mismo `libro_id` repetido en más de un renglón
- **THEN** el sistema responde HTTP 422 Unprocessable Entity impidiendo duplicaciones

#### Scenario: Venta rechazada por lista de renglones vacía
- **WHEN** se envía `POST /ventas` con una lista vacía de renglones
- **THEN** el sistema responde HTTP 422 Unprocessable Entity

### Requirement: Descuento atómico de stock y rollback por stock insuficiente
El sistema SHALL descontar el stock de cada libro vendido y generar movimientos de stock negativos; si para cualquiera de los libros el stock es menor a la cantidad solicitada, el sistema MUST realizar un rollback completo y responder HTTP 409 Conflict (RN-10, Caso C-15).

#### Scenario: Descuento exitoso registra movimientos de stock de salida
- **WHEN** se concreta una venta para libros con stock suficiente
- **THEN** el stock de cada libro disminuye en la cantidad vendida y se registra una fila en `movimiento_stock` con cantidad negativa por cada renglón

#### Scenario: Rollback total cuando el stock es insuficiente
- **WHEN** se intenta registrar una venta donde al menos un libro no posee stock suficiente
- **THEN** el sistema responde HTTP 409 Conflict, no persiste la venta ni los renglones, no crea movimientos de stock y el stock de todos los libros permanece inalterado

### Requirement: Despacho asincrónico simulado en segundo plano
El sistema SHALL encolar una tarea en segundo plano mediante BackgroundTasks para simular el despacho del comprobante (`await asyncio.sleep(0.5)`) que loguee en consola únicamente tras la confirmación exitosa de la venta.

#### Scenario: Despacho simulado únicamente tras confirmación exitosa
- **WHEN** la transacción de venta finaliza y se confirma en la base de datos
- **THEN** la tarea en segundo plano ejecuta la simulación asincrónica e imprime el comprobante sin demorar la respuesta HTTP 201

### Requirement: Aislamiento estricto de ventas por cliente
El sistema SHALL permitir al personal (ADMIN o VENDEDOR) consultar todas las ventas, mientras que a usuarios con rol CLIENTE únicamente les permitirá ver sus propias compras vía `/mis-ventas` o `/ventas/{id}`, respondiendo HTTP 403 Forbidden si intentan acceder a una venta de otro cliente (RN-14, Casos C-11 y C-12).

#### Scenario: Cliente consulta sus propias compras exitosamente
- **WHEN** un cliente autenticado solicita `GET /mis-ventas` o `GET /ventas/{id}` para una venta que le pertenece
- **THEN** el sistema responde HTTP 200 OK con el detalle de sus ventas

#### Scenario: Cliente intenta acceder a venta ajena y recibe 403
- **WHEN** un cliente autenticado intenta consultar mediante `GET /ventas/{id}` una venta perteneciente a otro cliente
- **THEN** el sistema responde HTTP 403 Forbidden impidiendo el acceso

#### Scenario: Personal administrativo consulta cualquier venta
- **WHEN** un usuario con rol ADMIN o VENDEDOR solicita `GET /ventas` o `GET /ventas/{id}` para cualquier venta
- **THEN** el sistema responde HTTP 200 OK sin restricciones de pertenencia
