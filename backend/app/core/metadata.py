"""Registro consolidado de todos los modelos de la base de datos para SQLModel y Alembic."""

from sqlmodel import SQLModel

from app.modules.usuarios.models import AsignacionRol, EventoSeguridad, IntentoAcceso, Usuario
from app.modules.editoriales.models import Editorial
from app.modules.generos.models import Genero
from app.modules.autores.models import Autor
from app.modules.libros.models import Libro, LibroAutor
from app.modules.clientes.models import Cliente, PerfilCliente
from app.modules.ventas.models import MovimientoStock, RenglonVenta, Venta

target_metadata = SQLModel.metadata

__all__ = [
    "SQLModel",
    "target_metadata",
    "Usuario",
    "AsignacionRol",
    "IntentoAcceso",
    "EventoSeguridad",
    "Editorial",
    "Genero",
    "Autor",
    "Libro",
    "LibroAutor",
    "Cliente",
    "PerfilCliente",
    "Venta",
    "RenglonVenta",
    "MovimientoStock",
]
