from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.core.dependencies import requiere_rol
from app.core.paginacion import PaginatedResponse, PaginationParams
from app.modules.libros.schemas import (
    LibroCreateRequest,
    LibroDetalleResponse,
    LibroUpdateRequest,
    MovimientoStockResponse,
    ReponerStockRequest,
)
from app.modules.libros.service import LibroService

public_router = APIRouter(prefix="/libros", tags=["Libros"])
protected_router = APIRouter(prefix="/libros", tags=["Libros"])


@public_router.get("", response_model=PaginatedResponse[LibroDetalleResponse])
async def listar_libros(
    titulo: str | None = Query(default=None, description="Filtro por título insensible a mayúsculas"),
    params: PaginationParams = Depends(),
    session: AsyncSession = Depends(get_session),
):
    service = LibroService(session)
    return await service.listar_catalogo(titulo=titulo, params=params)


@public_router.get("/{id}", response_model=LibroDetalleResponse)
async def obtener_libro(
    id: int,
    session: AsyncSession = Depends(get_session),
):
    service = LibroService(session)
    return await service.obtener_libro(id)


@protected_router.post(
    "",
    response_model=LibroDetalleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def crear_libro(
    data: LibroCreateRequest,
    usuario=Depends(requiere_rol("ADMIN")),
    session: AsyncSession = Depends(get_session),
):
    service = LibroService(session)
    return await service.crear_libro(data=data, usuario_id=usuario.id)


@protected_router.patch(
    "/{id}",
    response_model=LibroDetalleResponse,
)
async def actualizar_libro(
    id: int,
    data: LibroUpdateRequest,
    usuario=Depends(requiere_rol("ADMIN")),
    session: AsyncSession = Depends(get_session),
):
    service = LibroService(session)
    return await service.actualizar_libro(libro_id=id, data=data)


@protected_router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def borrar_libro(
    id: int,
    usuario=Depends(requiere_rol("ADMIN")),
    session: AsyncSession = Depends(get_session),
):
    service = LibroService(session)
    await service.borrar_libro(libro_id=id)


@protected_router.post(
    "/{id}/reponer",
    response_model=LibroDetalleResponse,
)
async def reponer_stock(
    id: int,
    data: ReponerStockRequest,
    usuario=Depends(requiere_rol("ADMIN")),
    session: AsyncSession = Depends(get_session),
):
    service = LibroService(session)
    return await service.reponer_stock(libro_id=id, data=data, usuario_id=usuario.id)


@protected_router.get(
    "/{id}/movimientos",
    response_model=PaginatedResponse[MovimientoStockResponse],
)
async def listar_movimientos_libro(
    id: int,
    params: PaginationParams = Depends(),
    usuario=Depends(requiere_rol("ADMIN")),
    session: AsyncSession = Depends(get_session),
):
    service = LibroService(session)
    return await service.listar_movimientos(libro_id=id, params=params)
