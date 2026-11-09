# Spec Delta

## Purpose

Asegura la inicialización determinística de datos requeridos para evaluación y el blindaje ante errores internos mediante traducción limpia de excepciones de base de datos.

## ADDED Requirements

### Requirement: Carga idempotente de datos iniciales requeridos
El sistema SHALL proveer un script de inicialización (`seed.py`) que pueble los usuarios con roles ('ADMIN', 'VENDEDOR', 'CLIENTE'), el catálogo (editoriales, géneros, autores y libros con stock inicial), clientes, la Venta 1 histórica con movimientos de salida asociados y el evento de seguridad inicial.

#### Scenario: Población limpia de usuarios catálogo clientes y venta inicial
- **WHEN** se ejecuta el script `seed.py` sobre una base vacía con esquema migrado
- **THEN** se crean los 5 usuarios solicitados, las 3 editoriales, 3 géneros, 6 autores, 5 libros con su stock inicial, 3 clientes, la Venta 1 con sus renglones y movimientos de stock, y un evento de auditoría

#### Scenario: Reejecución idempotente del script no duplica datos
- **WHEN** se ejecuta el script `seed.py` por segunda vez consecutiva
- **THEN** el script finaliza exitosamente sin duplicar registros ni violar restricciones de unicidad

### Requirement: Ocultamiento de detalles internos en errores de base de datos
El sistema SHALL interceptar excepciones de integridad (`IntegrityError`) y errores no controlados para responder con códigos HTTP estándar (409 Conflict o 500 Internal Server Error) ocultando trazas, nombres de restricciones y detalles internos del motor PostgreSQL (RN-01, RN-15).

#### Scenario: Captura de IntegrityError responde 409 con mensaje limpio
- **WHEN** una operación genera una violación de restricción de unicidad o clave foránea no capturada previamente
- **THEN** el manejador global intercepta el error y responde HTTP 409 Conflict con un mensaje comprensible de dominio sin exponer sintaxis SQL ni metadatos

#### Scenario: Errores no controlados responden 500 genérico sin trazas
- **WHEN** ocurre una excepción inesperada durante el procesamiento de una petición
- **THEN** el sistema responde HTTP 500 Internal Server Error con un mensaje genérico sin incluir stack traces en la respuesta
