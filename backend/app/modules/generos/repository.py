from typing import Sequence
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.repository import BaseRepository
from app.modules.generos.models import Genero


class GeneroRepository(BaseRepository[Genero]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Genero)

    async def get_by_nombre(self, nombre: str) -> Genero | None:
        stmt = select(Genero).where(Genero.nombre == nombre)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def listar(self, offset: int = 0, limit: int = 50) -> tuple[Sequence[Genero], int]:
        total_stmt = select(func.count()).select_from(Genero)
        total = (await self.session.execute(total_stmt)).scalar_one()

        stmt = select(Genero).order_by(Genero.id).offset(offset).limit(limit)
        items = (await self.session.execute(stmt)).scalars().all()
        return items, total
