from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.paginacion import PaginatedResponse, PaginationParams, paginate
from app.core.unit_of_work import UnitOfWork
from app.modules.clientes.repository import ClienteRepository
from app.modules.libros.repository import LibroRepository
from app.modules.usuarios.models import Usuario
from app.modules.ventas.models import MovimientoStock, RenglonVenta, Venta
from app.modules.ventas.repository import MovimientoStockRepository, VentaRepository
from app.modules.ventas.schemas import (
    ClienteSimpleResponse,
    LibroSimpleResponse,
    RenglonVentaCreateRequest,
    RenglonVentaResponse,
    VentaCreateRequest,
    VentaResponse,
)


class VentaService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.venta_repo = VentaRepository(session)
        self.cliente_repo = ClienteRepository(session)
        self.libro_repo = LibroRepository(session)
        self.movimiento_repo = MovimientoStockRepository(session)
        self.uow = UnitOfWork(session)

    def _map_venta(self, venta: Venta) -> VentaResponse:
        renglones = []
        if venta.renglones:
            for r in venta.renglones:
                renglones.append(
                    RenglonVentaResponse(
                        id=r.id,
                        venta_id=r.venta_id,
                        libro_id=r.libro_id,
                        cantidad=r.cantidad,
                        precio_unitario=r.precio_unitario,
                        subtotal=r.precio_unitario * r.cantidad,
                        libro=LibroSimpleResponse(
                            id=r.libro.id,
                            isbn=r.libro.isbn,
                            titulo=r.libro.titulo,
                        )
                        if r.libro
                        else None,
                    )
                )
        return VentaResponse(
            id=venta.id,
            cliente_id=venta.cliente_id,
            fecha=venta.fecha,
            total=venta.total,
            cliente=ClienteSimpleResponse(
                id=venta.cliente.id,
                nombre=venta.cliente.nombre,
                email=venta.cliente.email,
            )
            if venta.cliente
            else None,
            renglones=renglones,
        )

    async def crear_venta(
        self, data: VentaCreateRequest, usuario_id: int
    ) -> VentaResponse:
        cliente = await self.cliente_repo.get_by_id(data.cliente_id)
        if not cliente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente no encontrado",
            )

        async with self.uow:
            # 1. Validar stock de todos los libros involucrados antes de escribir
            libros_por_id = {}
            for item in data.renglones:
                libro = await self.libro_repo.get_detalle_vigente(item.libro_id)
                if not libro:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"El libro con ID {item.libro_id} no existe o fue descatalogado",
                    )
                if libro.stock < item.cantidad:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Stock insuficiente para '{libro.titulo}'. Stock disponible: {libro.stock}, solicitado: {item.cantidad} (RN-10)",
                    )
                libros_por_id[item.libro_id] = libro

            # 2. Crear cabecera de venta
            venta = Venta(cliente_id=data.cliente_id, total=Decimal("0.00"))
            await self.venta_repo.add(venta)

            total = Decimal("0.00")

            # 3. Procesar renglones, descuento de stock y movimientos
            for item in data.renglones:
                libro = libros_por_id[item.libro_id]
                precio_unitario = libro.precio
                subtotal = precio_unitario * item.cantidad
                total += subtotal

                renglon = RenglonVenta(
                    venta_id=venta.id,
                    libro_id=libro.id,
                    cantidad=item.cantidad,
                    precio_unitario=precio_unitario,
                )
                self.session.add(renglon)

                # Descuento en libro (RN-10, RN-11)
                libro.stock -= item.cantidad
                await self.libro_repo.update(libro)

                # Movimiento de stock de salida (cantidad negativa)
                movimiento = MovimientoStock(
                    libro_id=libro.id,
                    venta_id=venta.id,
                    usuario_id=usuario_id,
                    cantidad=-item.cantidad,
                    motivo=f"Venta #{venta.id}",
                )
                await self.movimiento_repo.add(movimiento)

            venta.total = total
            await self.venta_repo.update(venta)

        venta_cargada = await self.venta_repo.get_detalle(venta.id)
        return self._map_venta(venta_cargada)

    async def obtener_venta(
        self, venta_id: int, usuario: Usuario, roles_vigentes: list[str]
    ) -> VentaResponse:
        venta = await self.venta_repo.get_detalle(venta_id)
        if not venta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Venta no encontrada",
            )

        # Regla de aislamiento RN-14:
        es_personal = any(r in roles_vigentes for r in ("ADMIN", "VENDEDOR"))
        if not es_personal:
            cliente = await self.cliente_repo.get_by_usuario_id(usuario.id)
            if not cliente or venta.cliente_id != cliente.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No posee permisos para consultar esta venta (RN-14)",
                )

        return self._map_venta(venta)

    async def listar_ventas(
        self, params: PaginationParams
    ) -> PaginatedResponse[VentaResponse]:
        items, total = await self.venta_repo.listar_todas(
            offset=params.offset, limit=params.limit
        )
        mapped = [self._map_venta(v) for v in items]
        return paginate(mapped, total, params)

    async def listar_mis_ventas(
        self, usuario_id: int, params: PaginationParams
    ) -> PaginatedResponse[VentaResponse]:
        cliente = await self.cliente_repo.get_by_usuario_id(usuario_id)
        if not cliente:
            return paginate([], 0, params)

        items, total = await self.venta_repo.listar_por_cliente(
            cliente_id=cliente.id, offset=params.offset, limit=params.limit
        )
        mapped = [self._map_venta(v) for v in items]
        return paginate(mapped, total, params)
