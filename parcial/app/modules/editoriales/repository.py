from typing import Sequence
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.repository import BaseRepository
from app.modules.editoriales.models import Editorial


class EditorialRepository(BaseRepository[Editorial]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Editorial)

    async def get_by_nombre(self, nombre: str) -> Editorial | None:
        stmt = select(Editorial).where(Editorial.nombre == nombre)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def listar(self, offset: int = 0, limit: int = 50) -> tuple[Sequence[Editorial], int]:
        total_stmt = select(func.count()).select_from(Editorial)
        total = (await self.session.execute(total_stmt)).scalar_one()

        stmt = select(Editorial).order_by(Editorial.id).offset(offset).limit(limit)
        items = (await self.session.execute(stmt)).scalars().all()
        return items, total
