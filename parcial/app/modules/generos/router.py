from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.core.dependencies import requiere_rol
from app.core.paginacion import PaginatedResponse, PaginationParams, paginate
from app.core.unit_of_work import UnitOfWork
from app.modules.generos.models import Genero
from app.modules.generos.repository import GeneroRepository
from app.modules.generos.schemas import GeneroCreateRequest, GeneroResponse
from app.modules.libros.schemas import LibroDetalleResponse
from app.modules.libros.service import LibroService

public_router = APIRouter(prefix="/generos", tags=["Géneros"])
protected_router = APIRouter(prefix="/generos", tags=["Géneros"])


@public_router.get("", response_model=PaginatedResponse[GeneroResponse])
async def listar_generos(
    params: PaginationParams = Depends(),
    session: AsyncSession = Depends(get_session),
):
    repo = GeneroRepository(session)
    items, total = await repo.listar(offset=params.offset, limit=params.limit)
    mapped = [GeneroResponse.model_validate(g) for e in items for g in [e]]
    return paginate(mapped, total, params)


@public_router.get("/{id}", response_model=GeneroResponse)
async def obtener_genero(
    id: int,
    session: AsyncSession = Depends(get_session),
):
    repo = GeneroRepository(session)
    genero = await repo.get_by_id(id)
    if not genero:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Género no encontrado")
    return GeneroResponse.model_validate(genero)


@public_router.get("/{id}/libros", response_model=PaginatedResponse[LibroDetalleResponse])
async def listar_libros_por_genero(
    id: int,
    params: PaginationParams = Depends(),
    session: AsyncSession = Depends(get_session),
):
    service = LibroService(session)
    return await service.listar_por_genero(genero_id=id, params=params)


@protected_router.post(
    "",
    response_model=GeneroResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requiere_rol("ADMIN"))],
)
async def crear_genero(
    data: GeneroCreateRequest,
    session: AsyncSession = Depends(get_session),
):
    repo = GeneroRepository(session)
    existente = await repo.get_by_nombre(data.nombre)
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un género con el nombre '{data.nombre}' (RN-01)",
        )
    uow = UnitOfWork(session)
    async with uow:
        genero = Genero(nombre=data.nombre)
        await repo.add(genero)
    return GeneroResponse.model_validate(genero)


@protected_router.patch(
    "/{id}",
    response_model=GeneroResponse,
    dependencies=[Depends(requiere_rol("ADMIN"))],
)
async def actualizar_genero(
    id: int,
    data: GeneroCreateRequest,
    session: AsyncSession = Depends(get_session),
):
    repo = GeneroRepository(session)
    genero = await repo.get_by_id(id)
    if not genero:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Género no encontrado")

    existente = await repo.get_by_nombre(data.nombre)
    if existente and existente.id != id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un género con el nombre '{data.nombre}' (RN-01)",
        )

    uow = UnitOfWork(session)
    async with uow:
        genero.nombre = data.nombre
        await repo.update(genero)
    return GeneroResponse.model_validate(genero)
