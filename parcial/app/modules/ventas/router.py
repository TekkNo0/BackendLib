import asyncio
from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.core.dependencies import get_usuario_actual, requiere_rol
from app.core.paginacion import PaginatedResponse, PaginationParams
from app.modules.usuarios.models import Usuario
from app.modules.usuarios.repository import AsignacionRolRepository
from app.modules.ventas.schemas import VentaCreateRequest, VentaResponse
from app.modules.ventas.service import VentaService

router = APIRouter(tags=["Ventas"])


async def simular_despacho(venta_id: int, cliente_email: str) -> None:
    """Simula el envío asincrónico del comprobante en segundo plano (RN-10)."""
    await asyncio.sleep(0.5)
    print(f"[BACKGROUND] Comprobante para venta #{venta_id} despachado a {cliente_email}")


@router.post(
    "/ventas",
    response_model=VentaResponse,
    status_code=status.HTTP_201_CREATED,
)
async def crear_venta(
    data: VentaCreateRequest,
    background_tasks: BackgroundTasks,
    usuario: Usuario = Depends(requiere_rol("ADMIN", "VENDEDOR")),
    session: AsyncSession = Depends(get_session),
):
    service = VentaService(session)
    venta = await service.crear_venta(data=data, usuario_id=usuario.id)
    email_cliente = venta.cliente.email if venta.cliente else ""
    background_tasks.add_task(simular_despacho, venta.id, email_cliente)
    return venta


@router.get(
    "/ventas",
    response_model=PaginatedResponse[VentaResponse],
)
async def listar_ventas(
    params: PaginationParams = Depends(),
    usuario: Usuario = Depends(requiere_rol("ADMIN", "VENDEDOR")),
    session: AsyncSession = Depends(get_session),
):
    service = VentaService(session)
    return await service.listar_ventas(params=params)


@router.get(
    "/ventas/{id}",
    response_model=VentaResponse,
)
async def obtener_venta(
    id: int,
    usuario: Usuario = Depends(get_usuario_actual),
    session: AsyncSession = Depends(get_session),
):
    roles_repo = AsignacionRolRepository(session)
    roles_vigentes = await roles_repo.get_roles_vigentes(usuario.id)
    service = VentaService(session)
    return await service.obtener_venta(
        venta_id=id, usuario=usuario, roles_vigentes=roles_vigentes
    )


@router.get(
    "/mis-ventas",
    response_model=PaginatedResponse[VentaResponse],
)
async def listar_mis_ventas(
    params: PaginationParams = Depends(),
    usuario: Usuario = Depends(get_usuario_actual),
    session: AsyncSession = Depends(get_session),
):
    service = VentaService(session)
    return await service.listar_mis_ventas(usuario_id=usuario.id, params=params)
