from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.core.paginacion import PaginatedResponse, PaginationParams, paginate
from app.core.unit_of_work import UnitOfWork
from app.modules.clientes.models import Cliente
from app.modules.clientes.repository import ClienteRepository
from app.modules.clientes.schemas import ClienteCreateRequest, ClienteResponse

router = APIRouter(prefix="/clientes", tags=["Clientes"])


@router.get("/", response_model=PaginatedResponse[ClienteResponse])
@router.get("", response_model=PaginatedResponse[ClienteResponse], include_in_schema=False)
async def listar_clientes(
    params: PaginationParams = Depends(),
    session: AsyncSession = Depends(get_session),
):
    repo = ClienteRepository(session)
    items, total = await repo.listar(offset=params.offset, limit=params.limit)
    mapped = [ClienteResponse.model_validate(c) for c in items]
    return paginate(mapped, total, params)


@router.get("/{id}", response_model=ClienteResponse)
async def obtener_cliente(
    id: int,
    session: AsyncSession = Depends(get_session),
):
    repo = ClienteRepository(session)
    cliente = await repo.get_by_id(id)
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado",
        )
    return ClienteResponse.model_validate(cliente)


@router.post(
    "/",
    response_model=ClienteResponse,
    status_code=status.HTTP_201_CREATED,
)
@router.post(
    "",
    response_model=ClienteResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
async def crear_cliente(
    data: ClienteCreateRequest,
    session: AsyncSession = Depends(get_session),
):
    repo = ClienteRepository(session)
    existente = await repo.get_by_email(data.email)
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un cliente registrado con el email '{data.email}'",
        )

    uow = UnitOfWork(session)
    async with uow:
        cliente = Cliente(nombre=data.nombre.strip(), email=str(data.email).strip().lower())
        await repo.add(cliente)
    return ClienteResponse.model_validate(cliente)
