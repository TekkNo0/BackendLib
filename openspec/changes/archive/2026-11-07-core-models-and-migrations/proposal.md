# Proposal: Core Models and Migrations

## Why
El parcial requiere una base de datos relacional PostgreSQL con un esquema evolucionado mediante migraciones de Alembic (Ejercicio 2). El modelo debe incorporar borrado lógico en libros con unicidad de ISBN sólo entre vigentes, soporte de roles con vigencia e índice único parcial, tabla de movimientos de stock con clave foránea e índice, y auditoría e intentos de acceso, garantizando que el esquema se cree exclusivamente con Alembic y nunca con `create_all()`.

## What Changes
- Creación de modelos SQLModel/SQLAlchemy para todas las entidades en sus módulos respectivos:
  - `app/modules/usuarios/models.py`: `Usuario`, `AsignacionRol` (con CHECK de roles y UNIQUE parcial `(usuario_id, rol) WHERE revocada_en IS NULL`), `IntentoAcceso` (con índice `(email, ip, cuando)`), y `EventoSeguridad`.
  - `app/modules/editoriales/models.py`: `Editorial`.
  - `app/modules/generos/models.py`: `Genero`.
  - `app/modules/autores/models.py`: `Autor`.
  - `app/modules/libros/models.py`: `LibroAutor` y `Libro` (con `borrado_en timestamptz`, CHECKs `precio > 0` y `stock >= 0`, y UNIQUE parcial `(isbn) WHERE borrado_en IS NULL`).
  - `app/modules/clientes/models.py`: `Cliente` (con `usuario_id` nullable y UNIQUE, relación escalar 1-a-1 `usuario`) y `PerfilCliente`.
  - `app/modules/ventas/models.py`: `Venta`, `RenglonVenta` (CHECK `cantidad > 0`), y `MovimientoStock` (CHECK `cantidad <> 0`).
- Configuración de Alembic asincrónico: `alembic.ini` y `migrations/env.py` conectando con `asyncpg` y el `metadata` consolidado de SQLModel.
- Migración `0001_initial_tp`: Esquema base del TP (capítulos 1 a 4).
- Migración `0002_parcial_modelos`: Incorporación de tablas de seguridad (`usuario`, `asignacion_rol`, `intento_acceso`, `evento_seguridad`), tabla `movimiento_stock`, columnas `cliente.usuario_id`, `libro.borrado_en`, e índices únicos parciales. Cada migración comentada explicando su contenido y revisión.
- Pruebas automatizadas de modelos y migraciones.

## Capabilities

### New Capabilities
- `data-persistence`: Definición declarativa de modelos de datos SQLModel, restricciones de integridad a nivel de base de datos (CHECKs, FKs, tipos Decimal y timestamptz, índices parciales condicionales), y gestión versionada del ciclo de vida del esquema mediante Alembic asincrónico.

### Modified Capabilities
Ninguna.

## Impact
- Establece la capa Model para toda la aplicación y la estructura de tablas necesaria para autenticación, roles, stock y ventas.
