from typing import Sequence
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.repository import BaseRepository
from app.modules.autores.models import Autor


class AutorRepository(BaseRepository[Autor]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Autor)

    async def get_by_ids(self, ids: list[int]) -> Sequence[Autor]:
        if not ids:
            return []
        stmt = select(Autor).where(Autor.id.in_(ids))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def listar(self, offset: int = 0, limit: int = 50) -> tuple[Sequence[Autor], int]:
        total_stmt = select(func.count()).select_from(Autor)
        total = (await self.session.execute(total_stmt)).scalar_one()

        stmt = select(Autor).order_by(Autor.id).offset(offset).limit(limit)
        items = (await self.session.execute(stmt)).scalars().all()
        return items, total
