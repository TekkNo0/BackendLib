from typing import TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.libros.models import LibroAutor


class Autor(SQLModel, table=True):
    __tablename__ = "autor"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(nullable=False, index=True)
    nacionalidad: str = Field(nullable=False)

    libro_autores: list["LibroAutor"] = Relationship(
        back_populates="autor",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
