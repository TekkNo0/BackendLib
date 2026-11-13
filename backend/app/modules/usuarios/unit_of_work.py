from sqlalchemy.ext.asyncio import AsyncSession
from app.core.unit_of_work import UnitOfWork
from app.modules.clientes.repository import ClienteRepository
from app.modules.usuarios.repository import (
    AsignacionRolRepository,
    EventoSeguridadRepository,
    IntentoAccesoRepository,
    UsuarioRepository,
)


class UsuariosUnitOfWork(UnitOfWork):
    """Unit of Work del módulo usuarios y autenticación.
    
    Compone todos los repositorios que las operaciones del módulo necesitan,
    asegurando que todos compartan la misma sesión y transacción de base de datos.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session)
        self.usuarios = UsuarioRepository(session=session)
        self.roles = AsignacionRolRepository(session=session)
        self.intentos = IntentoAccesoRepository(session=session)
        self.eventos = EventoSeguridadRepository(session=session)
        self.clientes = ClienteRepository(session=session)
