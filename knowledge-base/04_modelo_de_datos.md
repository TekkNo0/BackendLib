# Modelo de Datos

## Dominios
- **Acceso y Seguridad**: `usuario`, `asignacion_rol`, `intento_acceso`, `evento_seguridad`.
- **Catálogo**: `editorial`, `genero`, `autor`, `libro`, `libro_autor`.
- **Clientes**: `cliente`, `perfil_cliente`.
- **Ventas e Inventario**: `venta`, `renglon_venta`, `movimiento_stock`.

## ERD (Diagrama Entidad-Relación)

```
[editorial] 1 ────< N [libro] >──── N [libro_autor] N ────< 1 [autor]
                        │  ▲
                        │  └── 1 ────< N [genero]
                        │
                        ├──── 1 ────< N [movimiento_stock]
                        │                    ▲
                        │                    │
                        │                    │ (venta_id nullable)
[usuario] 1 ──── 0..1 [cliente] 1 ────< N [venta] 1 ────< N [renglon_venta]
   │                      │
   ├─ 1 ──< N [asignacion_rol]   └─ 1 ── 0..1 [perfil_cliente]
   │
   ├─ (auditoría en evento_seguridad, independiente)
   └─ (registros en intento_acceso, independiente)
```

## Entidades y Restricciones de Base

### `usuario`
- `id`: `int` (PK, auto-incremental)
- `email`: `str` (UNIQUE, not null)
- `nombre`: `str` (not null)
- `password_hash`: `str` (not null, bcrypt)
- `activo`: `bool` (default `True`, not null)
- `debe_cambiar_password`: `bool` (default `False`, not null)

### `asignacion_rol`
- `id`: `int` (PK)
- `usuario_id`: `int` (FK `usuario.id`, not null)
- `rol`: `str` (CHECK `rol IN ('ADMIN', 'VENDEDOR', 'CLIENTE')`)
- `desde`: `datetime` (`timestamptz`, not null)
- `vence_en`: `datetime` (`timestamptz`, nullable)
- `revocada_en`: `datetime` (`timestamptz`, nullable)
- `otorgada_por`: `int` (FK `usuario.id`, nullable)
- **Restricción de unicidad**: Índice único parcial `(usuario_id, rol) WHERE revocada_en IS NULL`.

### `intento_acceso`
- `id`: `int` (PK)
- `cuando`: `datetime` (`timestamptz`, not null)
- `email`: `str` (not null)
- `ip`: `str` (not null)
- `exito`: `bool` (not null)
- **Índice**: `(email, ip, cuando)`.

### `evento_seguridad`
- `id`: `int` (PK)
- `cuando`: `datetime` (`timestamptz`, not null)
- `actor`: `str` (not null — texto, no FK, permite `'SISTEMA'`)
- `accion`: `str` (not null)

### `cliente`
- `id`: `int` (PK)
- `nombre`: `str` (not null)
- `email`: `str` (UNIQUE, not null)
- `usuario_id`: `int` (FK `usuario.id`, nullable, UNIQUE)
- Relación: `perfil` (`perfil_cliente`, 1 a 1), `ventas` (1 a N).

### `perfil_cliente`
- `id`: `int` (PK)
- `cliente_id`: `int` (FK `cliente.id`, not null, UNIQUE)
- `telefono`: `str` (not null)
- `direccion`: `str` (not null)

### `libro`
- `id`: `int` (PK)
- `isbn`: `str` (not null)
- `titulo`: `str` (not null)
- `precio`: `Decimal` (`Numeric(10, 2)`, CHECK `precio > 0`)
- `stock`: `int` (CHECK `stock >= 0`, default 0)
- `editorial_id`: `int` (FK `editorial.id`, not null)
- `genero_id`: `int` (FK `genero.id`, not null)
- `borrado_en`: `datetime` (`timestamptz`, nullable)
- **Restricción de unicidad**: Índice único parcial `(isbn) WHERE borrado_en IS NULL`.

### `movimiento_stock`
- `id`: `int` (PK)
- `libro_id`: `int` (FK `libro.id`, not null)
- `venta_id`: `int` (FK `venta.id`, nullable)
- `usuario_id`: `int` (FK `usuario.id`, not null)
- `cantidad`: `int` (CHECK `cantidad <> 0`)
- `motivo`: `str` (not null)
- `cuando`: `datetime` (`timestamptz`, not null)
- **Garantía**: Tabla de **sólo agregado** protegida por disparador en PostgreSQL (`BEFORE UPDATE OR DELETE ON movimiento_stock`).

### `venta`
- `id`: `int` (PK)
- `cliente_id`: `int` (FK `cliente.id`, not null)
- `fecha`: `datetime` (`timestamptz`, not null)
- `total`: `Decimal` (`Numeric(12, 2)`, not null)
- Relaciones: `cliente`, `renglones`.

### `renglon_venta`
- `id`: `int` (PK)
- `venta_id`: `int` (FK `venta.id`, not null)
- `libro_id`: `int` (FK `libro.id`, not null)
- `cantidad`: `int` (CHECK `cantidad > 0`, not null)
- `precio_unitario`: `Decimal` (`Numeric(10, 2)`, not null)

## Seed data inicial requerido (`seed.py`)
- **Usuarios**:
  - `admin@example.com` (ADMIN)
  - `admin2@example.com` (ADMIN)
  - `vendedor@example.com` (VENDEDOR)
  - `ana@example.com` (CLIENTE, vinculada a ficha de cliente Ana Paz)
  - `nuevo@example.com` (VENDEDOR, con `debe_cambiar_password = True`)
- **Catálogo**:
  - 3 Editoriales (ej. Sudamericana, Minotauro, Emecé)
  - 3 Géneros (ej. Novela, Cuento, Fantasía)
  - 6 Autores (ej. Cortázar, Borges, Bioy Casares, etc.)
  - 5 Libros:
    1. *Rayuela* (stock inicial 11, stock actual 10)
    2. *Antología de la literatura fantástica* (stock inicial 5, stock actual 5)
    3. *Ficciones* (stock inicial 10, stock actual 8)
    4. *Respiración artificial* (stock inicial 3, stock actual 3)
    5. *Bestiario* (stock inicial 1, stock actual 1)
- **Clientes**:
  - Lucía Fernández (con perfil, sin usuario)
  - Tomás Ríos (sin perfil, sin usuario)
  - Ana Paz (con usuario `ana@example.com`)
- **Venta 1**:
  - Cliente: Lucía Fernández
  - Vendedor: `vendedor@example.com`
  - Renglones: 1 Rayuela + 2 Ficciones (Total 69000.00)
  - Movimientos de stock de salida: -1 para Rayuela, -2 para Ficciones.
- **Historial de Seguridad**:
  - Un registro inicial con `actor = 'SISTEMA'` y `accion = 'Carga de los datos iniciales'`.
