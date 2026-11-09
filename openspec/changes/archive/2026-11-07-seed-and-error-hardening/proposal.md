# Proposal

## Why

Para cumplir con los requisitos evaluativos del Parcial de la UTN, la aplicación debe contar con un script de carga inicial de datos (`seed.py`) idempotente y representativo (usuarios de prueba con distintos roles y estados, catálogo completo, clientes, venta histórica y registro de auditoría). Asimismo, el sistema debe garantizar el blindaje y ocultamiento de detalles internos (RN-15 y RN-01), traduciendo cualquier colisión de unicidad o excepción de base de datos a respuestas HTTP claras (409 Conflict o 422 Unprocessable Entity) sin exponer nombres de tablas, columnas o mensajes nativos de PostgreSQL.

## What Changes

- Script de inicialización de datos en `parcial/seed.py`:
  - Población de usuarios requeridos: `admin@example.com`, `admin2@example.com`, `vendedor@example.com`, `ana@example.com` (con cliente asociado) y `nuevo@example.com` (con `debe_cambiar_password = True`).
  - Población de catálogo: 3 editoriales, 3 géneros, 6 autores y 5 libros con sus asociaciones y movimientos de stock inicial.
  - Población de clientes: Lucía Fernández (con perfil), Tomás Ríos (sin perfil), Ana Paz.
  - Población de Venta 1 histórica: Lucía Fernández atendida por `vendedor@example.com`, con renglones de Rayuela y Ficciones (total $69,000.00) y movimientos de stock de salida correspondientes.
  - Auditoría inicial en `evento_seguridad` con actor `'SISTEMA'`.
- Manejo global de excepciones en `parcial/app/core/exceptions.py` y registro en `parcial/main.py`:
  - Handler para `IntegrityError` de SQLAlchemy: traducción limpia a HTTP 409 con mensaje de dominio amigable, ocultando trazas y detalles internos de PostgreSQL (RN-01, RN-15).
  - Handler estandarizado para `RequestValidationError` (HTTP 422).
  - Handler global para errores no controlados (`Exception`) respondiendo HTTP 500 con mensaje genérico.
- Pruebas automatizadas en `parcial/test/test_seed_and_hardening.py`.

## Capabilities

### New Capabilities
- `system-resilience`: Carga de datos iniciales requeridos por consigna y traducción global de excepciones de infraestructura hacia respuestas HTTP de dominio limpias.

### Modified Capabilities
<!-- None -->

## Impact

- Nuevo script ejecutable `parcial/seed.py`.
- Nuevo módulo `parcial/app/core/exceptions.py`.
- Integración de manejadores de excepciones en `parcial/main.py`.
- Pruebas en `parcial/test/test_seed_and_hardening.py`.
