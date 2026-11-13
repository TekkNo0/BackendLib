from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.repository import BaseRepository
from app.modules.clientes.models import Cliente, PerfilCliente


class ClienteRepository(BaseRepository[Cliente]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=Cliente)

    async def get_by_email(self, email: str) -> Cliente | None:
        stmt = select(Cliente).where(Cliente.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_usuario_id(self, usuario_id: int) -> Cliente | None:
        stmt = select(Cliente).where(Cliente.usuario_id == usuario_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class PerfilClienteRepository(BaseRepository[PerfilCliente]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=PerfilCliente)
