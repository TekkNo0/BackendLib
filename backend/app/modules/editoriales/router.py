from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.core.dependencies import requiere_rol
from app.core.paginacion import PaginatedResponse, PaginationParams, paginate
from app.core.unit_of_work import UnitOfWork
from app.modules.editoriales.models import Editorial
from app.modules.editoriales.repository import EditorialRepository
from app.modules.editoriales.schemas import EditorialCreateRequest, EditorialResponse
from app.modules.libros.schemas import LibroDetalleResponse
from app.modules.libros.service import LibroService

public_router = APIRouter(prefix="/editoriales", tags=["Editoriales"])
protected_router = APIRouter(prefix="/editoriales", tags=["Editoriales"])


@public_router.get("/", response_model=PaginatedResponse[EditorialResponse])
@public_router.get("", response_model=PaginatedResponse[EditorialResponse], include_in_schema=False)
async def listar_editoriales(
    params: PaginationParams = Depends(),
    session: AsyncSession = Depends(get_session),
):
    repo = EditorialRepository(session)
    items, total = await repo.listar(offset=params.offset, limit=params.limit)
    mapped = [EditorialResponse.model_validate(e) for e in items]
    return paginate(mapped, total, params)


@public_router.get("/{id}", response_model=EditorialResponse)
async def obtener_editorial(
    id: int,
    session: AsyncSession = Depends(get_session),
):
    repo = EditorialRepository(session)
    editorial = await repo.get_by_id(id)
    if not editorial:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Editorial no encontrada")
    return EditorialResponse.model_validate(editorial)


@public_router.get("/{id}/libros", response_model=PaginatedResponse[LibroDetalleResponse])
async def listar_libros_por_editorial(
    id: int,
    params: PaginationParams = Depends(),
    session: AsyncSession = Depends(get_session),
):
    service = LibroService(session)
    return await service.listar_por_editorial(editorial_id=id, params=params)


@protected_router.post(
    "",
    response_model=EditorialResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requiere_rol("ADMIN"))],
)
async def crear_editorial(
    data: EditorialCreateRequest,
    session: AsyncSession = Depends(get_session),
):
    repo = EditorialRepository(session)
    existente = await repo.get_by_nombre(data.nombre)
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe una editorial con el nombre '{data.nombre}' (RN-01)",
        )
    uow = UnitOfWork(session)
    async with uow:
        editorial = Editorial(nombre=data.nombre)
        await repo.add(editorial)
    return EditorialResponse.model_validate(editorial)


@protected_router.patch(
    "/{id}",
    response_model=EditorialResponse,
    dependencies=[Depends(requiere_rol("ADMIN"))],
)
async def actualizar_editorial(
    id: int,
    data: EditorialCreateRequest,
    session: AsyncSession = Depends(get_session),
):
    repo = EditorialRepository(session)
    editorial = await repo.get_by_id(id)
    if not editorial:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Editorial no encontrada")

    existente = await repo.get_by_nombre(data.nombre)
    if existente and existente.id != id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe una editorial con el nombre '{data.nombre}' (RN-01)",
        )

    uow = UnitOfWork(session)
    async with uow:
        editorial.nombre = data.nombre
        await repo.update(editorial)
    return EditorialResponse.model_validate(editorial)
