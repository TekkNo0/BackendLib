from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from sqlalchemy import CheckConstraint, Column, DateTime, Index, text
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.clientes.models import Cliente


class Usuario(SQLModel, table=True):
    __tablename__ = "usuario"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, nullable=False)
    nombre: str = Field(nullable=False)
    password_hash: str = Field(nullable=False)
    activo: bool = Field(default=True, nullable=False)
    debe_cambiar_password: bool = Field(default=False, nullable=False)

    # Relaciones
    asignaciones: list["AsignacionRol"] = Relationship(
        back_populates="usuario",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "lazy": "selectin",
            "foreign_keys": "[AsignacionRol.usuario_id]",
        },
    )
    cliente: Optional["Cliente"] = Relationship(
        back_populates="usuario",
        sa_relationship_kwargs={"uselist": False},
    )


class AsignacionRol(SQLModel, table=True):
    __tablename__ = "asignacion_rol"
    __table_args__ = (
        CheckConstraint(
            "rol IN ('ADMIN', 'VENDEDOR', 'CLIENTE')",
            name="chk_rol_valido",
        ),
        Index(
            "uq_asignacion_rol_abierta",
            "usuario_id",
            "rol",
            unique=True,
            postgresql_where=text("revocada_en IS NULL"),
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuario.id", index=True, nullable=False)
    rol: str = Field(nullable=False)
    desde: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    vence_en: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    revocada_en: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    otorgada_por: int | None = Field(
        default=None,
        foreign_key="usuario.id",
        index=True,
        nullable=True,
    )

    usuario: Optional[Usuario] = Relationship(
        back_populates="asignaciones",
        sa_relationship_kwargs={"foreign_keys": "[AsignacionRol.usuario_id]"},
    )


class IntentoAcceso(SQLModel, table=True):
    __tablename__ = "intento_acceso"
    __table_args__ = (
        Index("ix_intento_acceso_email_ip_cuando", "email", "ip", "cuando"),
    )

    id: int | None = Field(default=None, primary_key=True)
    cuando: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    email: str = Field(nullable=False, index=True)
    ip: str = Field(nullable=False)
    exito: bool = Field(nullable=False)


class EventoSeguridad(SQLModel, table=True):
    __tablename__ = "evento_seguridad"

    id: int | None = Field(default=None, primary_key=True)
    cuando: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    actor: str = Field(nullable=False)  # Texto para permitir 'SISTEMA' o emails
    accion: str = Field(nullable=False)
