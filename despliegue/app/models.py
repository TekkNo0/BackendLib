from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy import CheckConstraint, Column, DateTime, Numeric
from sqlmodel import Field, Relationship, SQLModel


class Editorial(SQLModel, table=True):
    __tablename__ = "editorial"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(unique=True, index=True, nullable=False)

    libros: list["Libro"] = Relationship(back_populates="editorial")


class Genero(SQLModel, table=True):
    __tablename__ = "genero"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(unique=True, index=True, nullable=False)

    libros: list["Libro"] = Relationship(back_populates="genero")


class Autor(SQLModel, table=True):
    __tablename__ = "autor"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(nullable=False, index=True)
    nacionalidad: str = Field(nullable=False)

    libro_autores: list["LibroAutor"] = Relationship(back_populates="autor")


class LibroAutor(SQLModel, table=True):
    __tablename__ = "libro_autor"

    libro_id: int = Field(foreign_key="libro.id", primary_key=True, index=True)
    autor_id: int = Field(foreign_key="autor.id", primary_key=True, index=True)
    rol: str = Field(default="autor", nullable=False)
    orden: int = Field(default=1, nullable=False)

    libro: Optional["Libro"] = Relationship(back_populates="autores_asociados")
    autor: Optional["Autor"] = Relationship(back_populates="libro_autores")


class Libro(SQLModel, table=True):
    __tablename__ = "libro"
    __table_args__ = (
        CheckConstraint("precio > 0", name="chk_libro_precio_positivo"),
        CheckConstraint("stock >= 0", name="chk_libro_stock_no_negativo"),
    )

    id: int | None = Field(default=None, primary_key=True)
    isbn: str = Field(unique=True, index=True, nullable=False)
    titulo: str = Field(nullable=False, index=True)
    precio: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    stock: int = Field(default=0, nullable=False)
    editorial_id: int = Field(foreign_key="editorial.id", index=True, nullable=False)
    genero_id: int = Field(foreign_key="genero.id", index=True, nullable=False)

    editorial: Optional["Editorial"] = Relationship(back_populates="libros")
    genero: Optional["Genero"] = Relationship(back_populates="libros")
    autores_asociados: list[LibroAutor] = Relationship(back_populates="libro")


class Cliente(SQLModel, table=True):
    __tablename__ = "cliente"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(nullable=False)
    email: str = Field(unique=True, index=True, nullable=False)

    perfil: Optional["PerfilCliente"] = Relationship(
        back_populates="cliente",
        sa_relationship_kwargs={"uselist": False},
    )
    ventas: list["Venta"] = Relationship(back_populates="cliente")


class PerfilCliente(SQLModel, table=True):
    __tablename__ = "perfil_cliente"

    id: int | None = Field(default=None, primary_key=True)
    cliente_id: int = Field(foreign_key="cliente.id", unique=True, index=True, nullable=False)
    telefono: str = Field(nullable=False)
    direccion: str = Field(nullable=False)

    cliente: Optional[Cliente] = Relationship(back_populates="perfil")


class Venta(SQLModel, table=True):
    __tablename__ = "venta"

    id: int | None = Field(default=None, primary_key=True)
    cliente_id: int = Field(foreign_key="cliente.id", index=True, nullable=False)
    fecha: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    total: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))

    cliente: Optional[Cliente] = Relationship(back_populates="ventas")
    renglones: list["RenglonVenta"] = Relationship(back_populates="venta")


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
    libro: Optional[Libro] = Relationship()
