import math
from typing import Generic, Sequence, TypeVar
from fastapi import HTTPException, Query
from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: Sequence[T]
    total: int
    page: int
    size: int
    pages: int


class PaginationParams:
    """Parámetros de entrada estándar para paginación."""

    def __init__(
        self,
        page: int = Query(1, ge=1, description="Número de página (comienza en 1)"),
        size: int = Query(20, ge=1, le=100, description="Cantidad de elementos por página (1 a 100)"),
    ) -> None:
        self.page = page
        self.size = size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size

    @property
    def limit(self) -> int:
        return self.size


def paginate(items: Sequence[T], total: int, params: PaginationParams) -> PaginatedResponse[T]:
    """Crea la respuesta paginada y valida que la página solicitada no exceda el total."""
    pages = max(1, math.ceil(total / params.size))

    if total > 0 and params.page > pages:
        raise HTTPException(
            status_code=422,
            detail=f"La página {params.page} no existe: hay {pages}"
        )

    return PaginatedResponse(
        items=items,
        total=total,
        page=params.page,
        size=params.size,
        pages=pages,
    )
