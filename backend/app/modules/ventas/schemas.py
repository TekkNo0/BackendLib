from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class RenglonVentaCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    libro_id: int = Field(gt=0)
    cantidad: int = Field(gt=0)


class VentaCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cliente_id: int = Field(gt=0)
    renglones: list[RenglonVentaCreateRequest] = Field(min_length=1)

    @model_validator(mode="after")
    def validar_no_duplicados(self) -> "VentaCreateRequest":
        libro_ids = [r.libro_id for r in self.renglones]
        if len(libro_ids) != len(set(libro_ids)):
            raise ValueError("No se permiten libros repetidos en los renglones (RN-09).")
        return self


class ClienteSimpleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    email: str


class LibroSimpleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    isbn: str
    titulo: str


class RenglonVentaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    venta_id: int
    libro_id: int
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal | None = None
    libro: LibroSimpleResponse | None = None


class VentaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cliente_id: int
    fecha: datetime
    total: Decimal
    cliente: ClienteSimpleResponse | None = None
    renglones: list[RenglonVentaResponse] = []
