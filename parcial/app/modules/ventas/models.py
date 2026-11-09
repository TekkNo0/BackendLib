from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from sqlalchemy import CheckConstraint, Column, DateTime, Numeric
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.clientes.models import Cliente
    from app.modules.libros.models import Libro
    from app.modules.usuarios.models import Usuario


class Venta(SQLModel, table=True):
    __tablename__ = "venta"

    id: int | None = Field(default=None, primary_key=True)
    cliente_id: int = Field(foreign_key="cliente.id", index=True, nullable=False)
    fecha: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    total: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))

    cliente: Optional["Cliente"] = Relationship(back_populates="ventas")
    renglones: list["RenglonVenta"] = Relationship(
        back_populates="venta",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "lazy": "selectin"},
    )
    movimientos_stock: list["MovimientoStock"] = Relationship(back_populates="venta")


class RenglonVenta(SQLModel, table=True):
    __tablename__ = "renglon_venta"
    __table_args__ = (
        CheckConstraint("cantidad > 0", name="chk_renglon_cantidad_positiva"),
    )

    id: int | None = Field(default=None, primary_key=True)
    venta_id: int = Field(foreign_key="venta.id", index=True, nullable=False)
    libro_id: int = Field(foreign_key="libro.id", index=True, nullable=False)
    cantidad: int = Field(nullable=False)
    precio_unitario: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))

    venta: Optional[Venta] = Relationship(back_populates="renglones")
    libro: Optional["Libro"] = Relationship()


class MovimientoStock(SQLModel, table=True):
    __tablename__ = "movimiento_stock"
    __table_args__ = (
        CheckConstraint("cantidad <> 0", name="chk_movimiento_cantidad_no_cero"),
    )

    id: int | None = Field(default=None, primary_key=True)
    libro_id: int = Field(foreign_key="libro.id", index=True, nullable=False)
    venta_id: int | None = Field(default=None, foreign_key="venta.id", index=True, nullable=True)
    usuario_id: int = Field(foreign_key="usuario.id", index=True, nullable=False)
    cantidad: int = Field(nullable=False)
    motivo: str = Field(nullable=False)
    cuando: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    libro: Optional["Libro"] = Relationship(back_populates="movimientos_stock")
    venta: Optional[Venta] = Relationship(back_populates="movimientos_stock")
    usuario: Optional["Usuario"] = Relationship()
