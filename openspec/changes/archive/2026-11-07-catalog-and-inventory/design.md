# Design

## Context

El sistema ya cuenta con el modelo de datos y las migraciones necesarias para las tablas `editorial`, `genero`, `autor`, `libro`, `libro_autor` y `movimiento_stock` (con disparador append-only validado en C-03).
Ver `proposal.md` para motivación y alcance funcional.

## Goals / Non-Goals

**Goals:**
- Implementar DTOs Pydantic v2 estrictos (`extra="forbid"`) con validaciones precisas para rechazar `stock` en PATCH con 422 (RN-11).
- Implementar repositorios, Unit of Work y servicios para `libros`, `editoriales`, `generos` y `autores`.
- Implementar endpoints públicos para consulta y filtrado paginado (con precarga `selectinload` para evitar N+1).
- Implementar endpoints protegidos para administradores con RBAC y auditoría de stock.
- Garantizar la coexistencia histórica de libros borrados lógicamente y la reasignación de ISBN en nuevas altas (RN-13).

**Non-Goals:**
- Registrar ventas o descontar stock por transacciones de compra (correspondiente a C-07).
- Despacho asincrónico por BackgroundTasks (C-07).

## Decisions

### Decisión 1: Bloqueo explícito del campo `stock` en `PATCH /libros/{id}` (RN-11)
- **Elección**: Definir `LibroUpdateRequest` con `extra="forbid"` sin declarar el atributo `stock`, y sumar un `@model_validator(mode="before")` que verifique si `stock` fue enviado en el payload crudo para lanzar `ValueError("El stock sólo puede modificarse mediante movimientos")`.
- **Razón**: Asegurar inequívocamente que cualquier intento de enviar `"stock"` resulte en HTTP 422 y nunca pase desapercibido como campo ignorado.
- **Alternativas consideradas**: Ignorar silenciosamente el campo `stock` (`extra="ignore"`), lo cual violaría la consigna C-13 que exige responder 422.

### Decisión 2: Alta de libro con movimiento atómico inicial
- **Elección**: Dentro del `LibroService.crear_libro`, en el mismo `UnitOfWork`, persistir el `Libro`, asociar los autores en `libro_autor`, y si `stock_inicial > 0`, persistir inmediatamente un `MovimientoStock` (`tipo = 'ALTA'`, `motivo = "Stock inicial"`, `usuario_id = actual.id`).
- **Razón**: Mantiene la invariante obligatoria `libro.stock == SUM(movimiento_stock.cantidad)` desde el momento cero sin requerir pasos manuales posteriores.

### Decisión 3: Borrado lógico con soporte de reuso de ISBN (RN-13)
- **Elección**: `DELETE /libros/{id}` busca el libro donde `borrado_en IS NULL`. Si no existe o ya está borrado, responde 404 Not Found. Al borrarlo, asigna `borrado_en = datetime.now(timezone.utc)` y responde 204 No Content.
- **Razón**: El índice parcial único en PostgreSQL (`uq_libro_isbn_vigente WHERE borrado_en IS NULL`) permite registrar un nuevo libro con el mismo ISBN sin error de integridad.

### Decisión 4: Reposición atómica de inventario (RN-11, RN-13)
- **Elección**: `POST /libros/{id}/reponer` valida que `libro.borrado_en IS NULL` (si está borrado responde 409 Conflict). En una sola transacción, incrementa `libro.stock += cantidad` y agrega `MovimientoStock(cantidad=cantidad, motivo=motivo, usuario_id=actual.id)`.
- **Razón**: Garantiza consistencia atómica y trazabilidad obligatoria de quién y por qué repuso mercadería.

### Decisión 5: Precarga selectinload en listados y detalle
- **Elección**: Configurar las relaciones de `Libro` con `editorial`, `genero` y `autores_asociados.autor` usando `selectinload` en las consultas de catálogo.
- **Razón**: Evita el antipatrón de consultas N+1 al devolver el catálogo paginado.

## Risks / Trade-offs

- **[Riesgo de colisión de ISBN no vigente]**: Si una base no respeta el índice parcial, fallaría la inserción duplicada.
  → *Mitigación*: La migración Alembic 0002 definió explícitamente el índice parcial con `postgresql_where=text("borrado_en IS NULL")`.
- **[Riesgo de agotamiento de conexiones en endpoints de catálogo]**: Consultas públicas frecuentes podrían saturar el pool.
  → *Mitigación*: Los endpoints usan sesiones asincrónicas con context managers que cierran las conexiones inmediatamente tras devolver la respuesta.
