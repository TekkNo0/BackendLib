from typing import Sequence
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.repository import SoftDeleteRepository
from app.modules.libros.models import Libro, LibroAutor


class LibroRepository(SoftDeleteRepository[Libro]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Libro)

    def _eager_options(self):
        return [
            selectinload(Libro.editorial),
            selectinload(Libro.genero),
            selectinload(Libro.autores_asociados).selectinload(LibroAutor.autor),
        ]

    async def get_detalle_vigente(self, libro_id: int) -> Libro | None:
        stmt = (
            select(Libro)
            .options(*self._eager_options())
            .where(Libro.id == libro_id)
            .where(Libro.borrado_en.is_(None))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_detalle_any(self, libro_id: int) -> Libro | None:
        stmt = (
            select(Libro)
            .options(*self._eager_options())
            .where(Libro.id == libro_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_vigente_by_isbn(self, isbn: str) -> Libro | None:
        stmt = (
            select(Libro)
            .where(Libro.isbn == isbn)
            .where(Libro.borrado_en.is_(None))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def listar_catalogo(
        self, titulo: str | None = None, offset: int = 0, limit: int = 20
    ) -> tuple[Sequence[Libro], int]:
        total_stmt = (
            select(func.count())
            .select_from(Libro)
            .where(Libro.borrado_en.is_(None))
        )
        stmt = (
            select(Libro)
            .options(*self._eager_options())
            .where(Libro.borrado_en.is_(None))
            .order_by(Libro.id)
            .offset(offset)
            .limit(limit)
        )

        if titulo:
            total_stmt = total_stmt.where(Libro.titulo.ilike(f"%{titulo}%"))
            stmt = stmt.where(Libro.titulo.ilike(f"%{titulo}%"))

        total = (await self.session.execute(total_stmt)).scalar_one()
        items = (await self.session.execute(stmt)).scalars().all()
        return items, total

    async def listar_por_editorial(
        self, editorial_id: int, offset: int = 0, limit: int = 20
    ) -> tuple[Sequence[Libro], int]:
        total_stmt = (
            select(func.count())
            .select_from(Libro)
            .where(Libro.editorial_id == editorial_id)
            .where(Libro.borrado_en.is_(None))
        )
        stmt = (
            select(Libro)
            .options(*self._eager_options())
            .where(Libro.editorial_id == editorial_id)
            .where(Libro.borrado_en.is_(None))
            .order_by(Libro.id)
            .offset(offset)
            .limit(limit)
        )
        total = (await self.session.execute(total_stmt)).scalar_one()
        items = (await self.session.execute(stmt)).scalars().all()
        return items, total

    async def listar_por_genero(
        self, genero_id: int, offset: int = 0, limit: int = 20
    ) -> tuple[Sequence[Libro], int]:
        total_stmt = (
            select(func.count())
            .select_from(Libro)
            .where(Libro.genero_id == genero_id)
            .where(Libro.borrado_en.is_(None))
        )
        stmt = (
            select(Libro)
            .options(*self._eager_options())
            .where(Libro.genero_id == genero_id)
            .where(Libro.borrado_en.is_(None))
            .order_by(Libro.id)
            .offset(offset)
            .limit(limit)
        )
        total = (await self.session.execute(total_stmt)).scalar_one()
        items = (await self.session.execute(stmt)).scalars().all()
        return items, total

    async def listar_por_autor(
        self, autor_id: int, offset: int = 0, limit: int = 20
    ) -> tuple[Sequence[Libro], int]:
        total_stmt = (
            select(func.count())
            .select_from(Libro)
            .join(LibroAutor, LibroAutor.libro_id == Libro.id)
            .where(LibroAutor.autor_id == autor_id)
            .where(Libro.borrado_en.is_(None))
        )
        stmt = (
            select(Libro)
            .join(LibroAutor, LibroAutor.libro_id == Libro.id)
            .options(*self._eager_options())
            .where(LibroAutor.autor_id == autor_id)
            .where(Libro.borrado_en.is_(None))
            .order_by(Libro.id)
            .offset(offset)
            .limit(limit)
        )
        total = (await self.session.execute(total_stmt)).scalar_one()
        items = (await self.session.execute(stmt)).scalars().all()
        return items, total
