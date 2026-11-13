from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from sqlalchemy import CheckConstraint, Column, DateTime, Index, Numeric, text
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.autores.models import Autor
    from app.modules.editoriales.models import Editorial
    from app.modules.generos.models import Genero
    from app.modules.ventas.models import MovimientoStock


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
        Index(
            "uq_libro_isbn_vigente",
            "isbn",
            unique=True,
            postgresql_where=text("borrado_en IS NULL"),
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    isbn: str = Field(nullable=False, index=True)
    titulo: str = Field(nullable=False, index=True)
    precio: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    stock: int = Field(default=0, nullable=False)
    editorial_id: int = Field(foreign_key="editorial.id", index=True, nullable=False)
    genero_id: int | None = Field(default=None, foreign_key="genero.id", index=True, nullable=True)
    borrado_en: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )

    editorial: Optional["Editorial"] = Relationship(back_populates="libros")
    genero: Optional["Genero"] = Relationship(back_populates="libros")
    autores_asociados: list[LibroAutor] = Relationship(
        back_populates="libro",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "lazy": "selectin"},
    )
    movimientos_stock: list["MovimientoStock"] = Relationship(
        back_populates="libro",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
