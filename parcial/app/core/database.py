from collections.abc import AsyncGenerator
from fastapi import Request
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.core.config import Settings


def create_engine_and_session_factory(settings: Settings) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """Crea el motor asincrónico y la fábrica de sesiones respetando la configuración."""
    engine = create_async_engine(
        settings.database_url,
        echo=settings.SQL_ECHO,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        future=True,
    )
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return engine, session_factory


async def close_engine(engine: AsyncEngine) -> None:
    """Cierra limpiamente el pool de conexiones del motor."""
    await engine.dispose()


async def get_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Entrega una sesión asincrónica por petición desde app.state y la cierra al finalizar."""
    session_factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
