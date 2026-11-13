from types import TracebackType
from sqlalchemy.ext.asyncio import AsyncSession


class UnitOfWork:
    """Gestor de contexto asincrónico para transacciones atómicas.
    
    Regla:
    - Confirma (commit) al salir del bloque sin errores.
    - Revierte (rollback) si ocurre cualquier excepción y la relanza.
    - NO cierra la sesión porque fue creada y será cerrada por el ciclo de vida del request.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def __aenter__(self) -> "UnitOfWork":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            await self.session.rollback()
        else:
            await self.session.commit()
