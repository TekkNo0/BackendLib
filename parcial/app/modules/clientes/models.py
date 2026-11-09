from typing import TYPE_CHECKING, Optional
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.usuarios.models import Usuario
    from app.modules.ventas.models import Venta


class Cliente(SQLModel, table=True):
    __tablename__ = "cliente"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(nullable=False)
    email: str = Field(unique=True, index=True, nullable=False)
    usuario_id: int | None = Field(
        default=None,
        foreign_key="usuario.id",
        unique=True,
        index=True,
        nullable=True,
    )

    # Cliente.usuario devuelve un objeto escalar y no una lista
    usuario: Optional["Usuario"] = Relationship(
        back_populates="cliente",
        sa_relationship_kwargs={"uselist": False},
    )
    perfil: Optional["PerfilCliente"] = Relationship(
        back_populates="cliente",
        sa_relationship_kwargs={"uselist": False, "cascade": "all, delete-orphan"},
    )
    ventas: list["Venta"] = Relationship(back_populates="cliente")


class PerfilCliente(SQLModel, table=True):
    __tablename__ = "perfil_cliente"

    id: int | None = Field(default=None, primary_key=True)
    cliente_id: int = Field(
        foreign_key="cliente.id",
        unique=True,
        index=True,
        nullable=False,
    )
    telefono: str = Field(nullable=False)
    direccion: str = Field(nullable=False)

    cliente: Optional[Cliente] = Relationship(back_populates="perfil")
