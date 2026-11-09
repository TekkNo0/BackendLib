# Design: Foundation and Architecture

## Context
El parcial exige implementar la arquitectura en capas (Router → Service → UoW → Repository → Model) según las consignas del Ejercicio 1 y Ejercicio 6. Los componentes asincrónicos no deben inicializarse a nivel de importación de módulo (lo cual provocaría errores con el bucle de eventos en tests o al recargar), sino dentro del `lifespan` de FastAPI, guardándose en `app.state`. Además, la aplicación no debe contener secretos por defecto ni exponer detalles internos de la base de datos.

## Goals / Non-Goals

**Goals:**
- Estructurar el árbol de directorios `parcial/` con separación estricta en capas (`app/core/` y `app/modules/`).
- Proveer la configuración basada en `pydantic-settings` con `@computed_field` para la URL de asyncpg, garantizando la ausencia de secretos hardcodeados.
- Gestionar el ciclo de vida del motor `AsyncEngine` y `async_sessionmaker` mediante `lifespan`, almacenando las instancias en `app.state`.
- Implementar la jerarquía genérica de persistencia `BaseRepository[T]` y `SoftDeleteRepository[T]` que opera exclusivamente con `flush()` y nunca con `commit()`.
- Implementar el gestor de transacciones `UnitOfWork` base como context manager asincrónico que confirma en `__aexit__`, revierte ante excepciones y no cierra la sesión.
- Implementar el contrato y la función de cálculo del envoltorio de paginación `{items, total, page, size, pages}`.
- Implementar el módulo `health` con endpoints `/health/live` y `/health/ready` (SELECT 1 y código 503 ante fallas).

**Non-Goals:**
- Implementar modelos de negocio específicos (usuarios, libros, ventas) — diferidos a los changes C-02 y siguientes.
- Configurar el despliegue Docker y VPS — diferido al change C-09.
- Implementar el rate limiting de login o hashing de usuarios — diferido a C-04.

## Decisions

### D1: Gestión de Motor y Sesiones en `app.state` dentro de `lifespan`
- **Decisión**: El motor `create_async_engine` y `async_sessionmaker` se crean en la función `lifespan(app: FastAPI)` y se guardan en `app.state.engine` y `app.state.session_factory`.
- **Razón**: Evita la creación de descriptores de sockets o conexiones de base de datos antes de que el event loop de `asyncio` esté corriendo. Permite que `app.state.engine.dispose()` se invoque limpiamente en el shutdown.
- **Alternativas consideradas**:
  - *Módulos globales (singleton a nivel de archivo)*: Descartado porque rompe la portabilidad en pytest y falla si el bucle de eventos se reinicia.

### D2: Separación de Responsabilidades entre UnitOfWork y Repositorios
- **Decisión**: Los repositorios solo reciben la sesión (`AsyncSession`) y la clase del modelo (`type[T]`), ejecutan consultas y llaman a `await session.flush()` en operaciones de inserción/modificación. Nunca ejecutan `commit()`. El `UnitOfWork` base implementa `__aenter__` y `__aexit__`, llamando a `await session.commit()` al finalizar sin errores o `await session.rollback()` si se captura una excepción. La sesión se cierra en el generador de dependencia `get_session` (request lifecycle).
- **Razón**: Cumple el requisito explícito del Ejercicio 6 del parcial, garantizando atomicidad y evitando commits parciales prematuros.
- **Alternativas consideradas**:
  - *Commit en el repositorio*: Descartado expresamente por la consigna ("ningún repositorio confirma").

### D3: SoftDeleteRepository específico para entidades con borrado lógico
- **Decisión**: `SoftDeleteRepository[T]` hereda de `BaseRepository[T]` e intercepta las lecturas para inyectar `where(model.borrado_en.is_(None))`. Añade métodos explícitos `soft_delete(id)` y `get_by_id_including_deleted(id)`.
- **Razón**: Permite que entidades como `Libro` puedan ser dadas de baja sin eliminar su registro físico, preservando la integridad referencial en ventas históricas (RN-13).

### D4: Envoltorio de Paginación Rígido con Validación de Rango
- **Decisión**: El contrato de paginación devuelve `{items: list, total: int, page: int, size: int, pages: int}`. Si `page > pages` (cuando total > 0), se lanza una excepción HTTP 422 con mensaje descriptivo ("La página X no existe: hay Y"). Si `total == 0`, devuelve `page=1, pages=1, items=[]`.
- **Razón**: Cumple la especificación de la sección 2.9 y Ejercicio 3 del parcial.

## Risks / Trade-offs

- **[Riesgo: Sesiones colgadas ante excepciones en handlers]** → *Mitigación*: `get_session` utiliza un bloque `try ... finally` asincrónico para garantizar `await session.close()` independientemente del resultado del request.
- **[Riesgo: Contraseñas o secretos vacíos en producción]** → *Mitigación*: `Settings` no provee valores por defecto para `POSTGRES_PASSWORD` ni `SECRET_KEY`, forzando el fallo inmediato en el arranque si no están configuradas en el entorno.
