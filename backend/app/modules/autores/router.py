from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.core.dependencies import requiere_rol
from app.core.paginacion import PaginatedResponse, PaginationParams, paginate
from app.core.unit_of_work import UnitOfWork
from app.modules.autores.models import Autor
from app.modules.autores.repository import AutorRepository
from app.modules.autores.schemas import AutorCreateRequest, AutorResponse
from app.modules.libros.schemas import LibroDetalleResponse
from app.modules.libros.service import LibroService

public_router = APIRouter(prefix="/autores", tags=["Autores"])
protected_router = APIRouter(prefix="/autores", tags=["Autores"])


@public_router.get("/", response_model=PaginatedResponse[AutorResponse])
@public_router.get("", response_model=PaginatedResponse[AutorResponse], include_in_schema=False)
async def listar_autores(
    params: PaginationParams = Depends(),
    session: AsyncSession = Depends(get_session),
):
    repo = AutorRepository(session)
    items, total = await repo.listar(offset=params.offset, limit=params.limit)
    mapped = [AutorResponse.model_validate(a) for a in items]
    return paginate(mapped, total, params)


@public_router.get("/{id}", response_model=AutorResponse)
async def obtener_autor(
    id: int,
    session: AsyncSession = Depends(get_session),
):
    repo = AutorRepository(session)
    autor = await repo.get_by_id(id)
    if not autor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Autor no encontrado")
    return AutorResponse.model_validate(autor)


@public_router.get("/{id}/libros", response_model=PaginatedResponse[LibroDetalleResponse])
async def listar_libros_por_autor(
    id: int,
    params: PaginationParams = Depends(),
    session: AsyncSession = Depends(get_session),
):
    service = LibroService(session)
    return await service.listar_por_autor(autor_id=id, params=params)


@protected_router.post(
    "",
    response_model=AutorResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requiere_rol("ADMIN"))],
)
async def crear_autor(
    data: AutorCreateRequest,
    session: AsyncSession = Depends(get_session),
):
    repo = AutorRepository(session)
    uow = UnitOfWork(session)
    async with uow:
        autor = Autor(nombre=data.nombre, nacionalidad=data.nacionalidad)
        await repo.add(autor)
    return AutorResponse.model_validate(autor)


@protected_router.patch(
    "/{id}",
    response_model=AutorResponse,
    dependencies=[Depends(requiere_rol("ADMIN"))],
)
async def actualizar_autor(
    id: int,
    data: AutorCreateRequest,
    session: AsyncSession = Depends(get_session),
):
    repo = AutorRepository(session)
    autor = await repo.get_by_id(id)
    if not autor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Autor no encontrado")

    uow = UnitOfWork(session)
    async with uow:
        autor.nombre = data.nombre
        autor.nacionalidad = data.nacionalidad
        await repo.update(autor)
    return AutorResponse.model_validate(autor)
