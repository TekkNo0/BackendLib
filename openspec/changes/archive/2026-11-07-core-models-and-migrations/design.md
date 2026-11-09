# Design: Core Models and Migrations

## Context
El parcial evoluciona el modelo del TP de la librería incorporando acceso por roles, auditoría, intentos de acceso, borrado lógico de libros y movimientos de stock (Páginas 4, 5, 6 del PDF). Además, el Ejercicio 2 impone que el esquema se cree exclusivamente con migraciones de Alembic sin utilizar jamás `create_all()`.

## Goals / Non-Goals

**Goals:**
- Implementar los modelos de tabla con SQLModel en sus módulos funcionales (`usuarios`, `editoriales`, `generos`, `autores`, `libros`, `clientes`, `ventas`).
- Garantizar que los montos monetarios utilicen `Decimal` en Python y `Numeric` en base, y las fechas nuevas utilicen `timestamptz`.
- Declarar índices únicos parciales con `postgresql_where`: `(usuario_id, rol) WHERE revocada_en IS NULL` y `isbn WHERE borrado_en IS NULL`.
- Definir la relación 1-a-1 opcional entre `Cliente` y `Usuario` asegurando que `cliente.usuario` devuelva un objeto escalar o `None` (`uselist=False`).
- Configurar Alembic con soporte asincrónico para `asyncpg` y versionar el esquema con migraciones documentadas (`0001_initial_tp` y `0002_parcial_modelos`).

**Non-Goals:**
- Implementar el disparador PostgreSQL de sólo agregado sobre `movimiento_stock` (asignado a C-03).
- Implementar repositorios específicos de dominio, contratos Pydantic ni routers CRUD (asignados a C-04, C-05, C-06, C-07).

## Decisions

### D1: Modularización de Modelos y Re-exportación Consolidada
- **Decisión**: Los modelos residen en `app/modules/<modulo>/models.py`. Para Alembic y SQLModel, se crea `app/core/metadata.py` (o similar) que importa todos los modelos, permitiendo que `target_metadata = SQLModel.metadata` en `env.py` reconozca todas las entidades.
- **Razón**: Mantiene la arquitectura por módulos exigida en la página 8 del PDF y previene importaciones circulares.

### D2: Índices Únicos Parciales en PostgreSQL (`postgresql_where`)
- **Decisión**: En `AsignacionRol`, se declara `Index("uq_asignacion_rol_abierta", "usuario_id", "rol", unique=True, postgresql_where=text("revocada_en IS NULL"))`. En `Libro`, `Index("uq_libro_isbn_vigente", "isbn", unique=True, postgresql_where=text("borrado_en IS NULL"))`.
- **Razón**: Cumple estrictamente RN-01, RN-03 y RN-13, permitiendo reutilizar el ISBN de libros descatalogados y mantener el historial de roles revocados.

### D3: Relación Escalar `Cliente.usuario`
- **Decisión**: En el modelo `Cliente`, la relación `usuario` se declara con `sa_relationship_kwargs={"uselist": False}` apuntando a `Usuario`.
- **Razón**: Cumple el requisito explícito del Ejercicio 2 ("Cliente.usuario devuelve un objeto y no una lista").

### D4: Separación de Migraciones 0001 (TP Base) y 0002 (Parcial)
- **Decisión**: La migración `0001_initial_tp.py` define el baseline de las tablas originales del TP (catálogo, clientes, ventas sin borrado lógico ni usuarios). La migración `0002_parcial_modelos.py` incorpora las tablas de seguridad, movimientos de stock, campos `borrado_en` y `usuario_id`, e índices parciales.
- **Razón**: Respeta la evolución histórica requerida en el Ejercicio 2 ("A las migraciones del TP se suman dos nuevas").

## Risks / Trade-offs

- **[Riesgo: Índices parciales no soportados en SQLite durante tests ligeros]** → *Mitigación*: La suite de pruebas usa PostgreSQL con la base configurada en el entorno o mocks controlados, y Alembic utiliza el dialecto nativo de PostgreSQL.
- **[Riesgo: Omitir índices en claves foráneas]** → *Mitigación*: Cada relación ForeignKey declara explícitamente `index=True` en SQLModel o un `Index` dedicado, conforme a la sección 4.10 del PDF.
