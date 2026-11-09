from datetime import datetime, timezone
from typing import Any, Generic, Sequence, TypeVar
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Repositorio base genérico para operaciones CRUD asincrónicas.
    
    Recibe explícitamente la sesión y la clase del modelo debido al type erasure
    de genéricos en tiempo de ejecución en Python.
    """

    def __init__(self, session: AsyncSession, model: type[T]) -> None:
        self.session = session
        self.model = model

    async def get_by_id(self, id: Any) -> T | None:
        """Obtiene una entidad por su clave primaria."""
        return await self.session.get(self.model, id)

    async def get_all(self, offset: int = 0, limit: int = 100) -> Sequence[T]:
        """Obtiene un conjunto de entidades con soporte para paginación."""
        stmt = select(self.model).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(self) -> int:
        """Cuenta el total de entidades existentes."""
        stmt = select(func.count()).select_from(self.model)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def add(self, entity: T) -> T:
        """Agrega una nueva entidad y ejecuta flush para obtener IDs generados sin confirmar."""
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def update(self, entity: T) -> T:
        """Actualiza una entidad y hace flush sin commit."""
        await self.session.flush()
        return entity

    async def delete(self, entity: T) -> None:
        """Elimina una entidad físicamente y hace flush."""
        await self.session.delete(entity)
        await self.session.flush()


class SoftDeleteRepository(BaseRepository[T]):
    """Repositorio para entidades que implementan borrado lógico (e.g. Libro con borrado_en)."""

    async def get_by_id(self, id: Any) -> T | None:
        """Obtiene la entidad solo si no está dada de baja lógicamente."""
        stmt = (
            select(self.model)
            .where(getattr(self.model, "id") == id)
            .where(getattr(self.model, "borrado_en").is_(None))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_including_deleted(self, id: Any) -> T | None:
        """Obtiene la entidad por id sin filtrar si está borrada lógicamente."""
        return await self.session.get(self.model, id)

    async def get_all(self, offset: int = 0, limit: int = 100) -> Sequence[T]:
        """Obtiene entidades activas (borrado_en IS NULL)."""
        stmt = (
            select(self.model)
            .where(getattr(self.model, "borrado_en").is_(None))
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(self) -> int:
        """Cuenta únicamente las entidades activas."""
        stmt = (
            select(func.count())
            .select_from(self.model)
            .where(getattr(self.model, "borrado_en").is_(None))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def soft_delete(self, entity: T) -> T:
        """Marca la entidad como borrada con fecha y hora actual en UTC y hace flush."""
        setattr(entity, "borrado_en", datetime.now(timezone.utc))
        await self.session.flush()
        return entity
