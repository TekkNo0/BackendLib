import os
from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from app.core.config import Settings
from app.core.paginacion import PaginationParams, paginate
from app.core.repository import BaseRepository, SoftDeleteRepository
from app.core.unit_of_work import UnitOfWork


def test_settings_missing_required_secrets_fails_fast():
    """Valida que si falta POSTGRES_PASSWORD o SECRET_KEY, Settings falla inmediatamente."""
    # Guardar variables previas
    old_env = os.environ.copy()
    try:
        os.environ.pop("POSTGRES_PASSWORD", None)
        os.environ.pop("SECRET_KEY", None)
        
        with pytest.raises(ValidationError):
            Settings(_env_file=None)
    finally:
        os.environ.clear()
        os.environ.update(old_env)


def test_settings_computed_database_url():
    """Valida que database_url se compute con postgresql+asyncpg."""
    s = Settings(
        POSTGRES_USER="testuser",
        POSTGRES_PASSWORD="testpassword",
        POSTGRES_DB="testdb",
        POSTGRES_HOST="dbhost",
        POSTGRES_PORT=5433,
        SECRET_KEY="supersecret",
        _env_file=None,
    )
    assert s.database_url == "postgresql+asyncpg://testuser:testpassword@dbhost:5433/testdb"


def test_pagination_envelope_and_range_validation():
    """Valida el contrato {items, total, page, size, pages} y el error 422 si page > pages."""
    # Caso 1: Datos normales
    params = PaginationParams(page=1, size=2)
    resp = paginate(items=["item1", "item2"], total=5, params=params)
    assert resp.total == 5
    assert resp.page == 1
    assert resp.size == 2
    assert resp.pages == 3
    assert len(resp.items) == 2

    # Caso 2: Cero resultados -> 1 página vacía
    resp_empty = paginate(items=[], total=0, params=PaginationParams(page=1, size=10))
    assert resp_empty.total == 0
    assert resp_empty.page == 1
    assert resp_empty.pages == 1
    assert resp_empty.items == []

    # Caso 3: Pedir página más allá de la última -> 422
    with pytest.raises(HTTPException) as exc_info:
        paginate(items=[], total=5, params=PaginationParams(page=4, size=2))
    assert exc_info.value.status_code == 422
    assert "La página 4 no existe: hay 3" in exc_info.value.detail


@pytest.mark.asyncio
async def test_repository_calls_flush_and_not_commit():
    """Valida que los repositorios llamen a flush() y nunca a commit()."""
    mock_session = AsyncMock()
    repo = BaseRepository(session=mock_session, model=dict)
    
    entity = {"name": "test"}
    await repo.add(entity)
    mock_session.add.assert_called_once_with(entity)
    mock_session.flush.assert_awaited_once()
    mock_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_unit_of_work_commits_on_success_and_rolls_back_on_error():
    """Valida que UnitOfWork haga commit en salida limpia y rollback ante excepción."""
    mock_session = AsyncMock()
    
    # Caso éxito
    async with UnitOfWork(mock_session):
        pass
    mock_session.commit.assert_awaited_once()
    mock_session.rollback.assert_not_called()
    mock_session.close.assert_not_called()

    # Caso excepción
    mock_session.reset_mock()
    with pytest.raises(RuntimeError):
        async with UnitOfWork(mock_session):
            raise RuntimeError("Fallo forzado en bloque de negocio")
    mock_session.rollback.assert_awaited_once()
    mock_session.commit.assert_not_called()
    mock_session.close.assert_not_called()


@pytest.mark.asyncio
async def test_health_live_endpoint():
    """Valida que GET /health/live responda 200 sin tocar la base de datos."""
    from httpx import ASGITransport, AsyncClient
    from main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/health/live")
        assert resp.status_code == 200
        assert resp.json() == {"status": "live"}


@pytest.mark.asyncio
async def test_health_ready_endpoint_success_and_failure():
    """Valida que GET /health/ready responda 200 si la base responde y 503 si falla."""
    from httpx import ASGITransport, AsyncClient
    from main import app
    from app.core.database import get_session

    # Simular base respondiendo SELECT 1
    mock_session_ok = AsyncMock()
    mock_session_ok.execute.return_value = None

    async def override_get_session_ok():
        yield mock_session_ok

    app.dependency_overrides[get_session] = override_get_session_ok
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/health/ready")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ready"}

    # Simular base caída
    mock_session_fail = AsyncMock()
    mock_session_fail.execute.side_effect = ConnectionRefusedError("PostgreSQL caído")

    async def override_get_session_fail():
        yield mock_session_fail

    app.dependency_overrides[get_session] = override_get_session_fail
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/health/ready")
        assert resp.status_code == 503
        assert "Base de datos no disponible" in resp.json()["detail"]

    app.dependency_overrides.clear()

