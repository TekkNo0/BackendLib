from datetime import datetime
from decimal import Decimal
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.modules.autores.schemas import AutorResponse
from app.modules.editoriales.schemas import EditorialResponse
from app.modules.generos.schemas import GeneroResponse


class AutoriaCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    autor_id: int = Field(gt=0)
    rol: Literal["autor", "coautor", "traductor", "ilustrador"] = "autor"
    orden: int = Field(default=1, ge=1)


class LibroCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    isbn: str = Field(min_length=1, max_length=20)
    titulo: str = Field(min_length=1, max_length=255)
    precio: Decimal = Field(gt=0)
    editorial_id: int
    genero_id: int | None = None
    autores: list[AutoriaCreateRequest] | None = None
    autores_ids: list[int] | None = None
    stock_inicial: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def normalizar_autores(self) -> "LibroCreateRequest":
        if self.autores and len(self.autores) > 0:
            return self
        if self.autores_ids and len(self.autores_ids) > 0:
            self.autores = [
                AutoriaCreateRequest(autor_id=aid, rol="autor", orden=idx)
                for idx, aid in enumerate(self.autores_ids, start=1)
            ]
            return self
        raise ValueError("Debe indicar al menos un autor.")


class LibroUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titulo: str | None = Field(default=None, min_length=1, max_length=255)
    precio: Decimal | None = Field(default=None, gt=0)

    @model_validator(mode="before")
    @classmethod
    def rechazar_campo_stock(cls, data: Any) -> Any:
        if isinstance(data, dict) and "stock" in data:
            raise ValueError("El stock no puede modificarse por este endpoint (RN-11).")
        return data


class LibroResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    isbn: str
    titulo: str
    precio: Decimal
    stock: int
    editorial_id: int
    genero_id: int | None = None
    borrado_en: datetime | None = None


class AutorEnLibroResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    nacionalidad: str
    rol: str = "autor"
    orden: int = 1


class LibroDetalleResponse(LibroResponse):
    editorial: EditorialResponse | None = None
    genero: GeneroResponse | None = None
    autores: list[AutorEnLibroResponse] = []


class ReponerStockRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cantidad: int = Field(gt=0)
    motivo: str = Field(default="Reposición de inventario", min_length=1, max_length=255)


class MovimientoStockResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    libro_id: int
    venta_id: int | None = None
    usuario_id: int
    cantidad: int
    motivo: str
    cuando: datetime
