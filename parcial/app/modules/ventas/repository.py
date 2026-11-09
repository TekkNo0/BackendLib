from typing import Sequence
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.repository import BaseRepository
from app.modules.ventas.models import MovimientoStock, RenglonVenta, Venta


class MovimientoStockRepository(BaseRepository[MovimientoStock]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, MovimientoStock)

    async def listar_por_libro(
        self, libro_id: int, offset: int = 0, limit: int = 50
    ) -> tuple[Sequence[MovimientoStock], int]:
        total_stmt = (
            select(func.count())
            .select_from(MovimientoStock)
            .where(MovimientoStock.libro_id == libro_id)
        )
        total = (await self.session.execute(total_stmt)).scalar_one()

        stmt = (
            select(MovimientoStock)
            .where(MovimientoStock.libro_id == libro_id)
            .order_by(MovimientoStock.cuando.desc())
            .offset(offset)
            .limit(limit)
        )
        items = (await self.session.execute(stmt)).scalars().all()
        return items, total


class VentaRepository(BaseRepository[Venta]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Venta)

    def _eager_options(self):
        return [
            selectinload(Venta.cliente),
            selectinload(Venta.renglones).selectinload(RenglonVenta.libro),
        ]

    async def get_detalle(self, venta_id: int) -> Venta | None:
        stmt = (
            select(Venta)
            .options(*self._eager_options())
            .where(Venta.id == venta_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def listar_todas(
        self, offset: int = 0, limit: int = 20
    ) -> tuple[Sequence[Venta], int]:
        total_stmt = select(func.count()).select_from(Venta)
        total = (await self.session.execute(total_stmt)).scalar_one()

        stmt = (
            select(Venta)
            .options(*self._eager_options())
            .order_by(Venta.fecha.desc())
            .offset(offset)
            .limit(limit)
        )
        items = (await self.session.execute(stmt)).scalars().all()
        return items, total

    async def listar_por_cliente(
        self, cliente_id: int, offset: int = 0, limit: int = 20
    ) -> tuple[Sequence[Venta], int]:
        total_stmt = (
            select(func.count())
            .select_from(Venta)
            .where(Venta.cliente_id == cliente_id)
        )
        total = (await self.session.execute(total_stmt)).scalar_one()

        stmt = (
            select(Venta)
            .options(*self._eager_options())
            .where(Venta.cliente_id == cliente_id)
            .order_by(Venta.fecha.desc())
            .offset(offset)
            .limit(limit)
        )
        items = (await self.session.execute(stmt)).scalars().all()
        return items, total
