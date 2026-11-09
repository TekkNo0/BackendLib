from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from fastapi import status
import pytest
from httpx import ASGITransport, AsyncClient
from main import app
from app.core.dependencies import get_usuario_actual, get_usuarios_uow
from app.modules.usuarios.models import AsignacionRol, Usuario
from app.modules.usuarios.schemas import AsignarRolRequest


def test_asignar_rol_fecha_validations_return_422():
    """Valida que fechas de vencimiento pasadas o sin zona horaria den 422 (Ejercicio 5)."""
    # 1. Fecha en el pasado con zona
    pasado = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    with pytest.raises(ValueError) as exc1:
        AsignarRolRequest(rol="VENDEDOR", vence_en=pasado)
    assert "en el futuro" in str(exc1.value)

    # 2. Fecha sin zona horaria
    sin_zona = "2028-12-31T23:59:59"
    with pytest.raises(ValueError) as exc2:
        AsignarRolRequest(rol="VENDEDOR", vence_en=sin_zona)
    assert "zona horaria" in str(exc2.value)


@pytest.mark.asyncio
async def test_autoproteccion_admin_no_se_revoca_a_si_mismo():
    """Valida que un ADMIN no pueda revocarse su propio rol ADMIN: 409 (RN-05)."""
    from app.core.database import get_session

    admin_mock = Usuario(
        id=1,
        email="admin@example.com",
        nombre="Admin Uno",
        password_hash="hash",
        activo=True,
        debe_cambiar_password=False,
    )
    mock_uow = MagicMock()
    mock_uow.usuarios = AsyncMock()
    mock_uow.usuarios.get_by_id.return_value = admin_mock
    mock_uow.roles = AsyncMock()

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = ["ADMIN"]
    mock_session = AsyncMock()
    mock_session.execute.return_value = mock_result

    async def override_get_session():
        yield mock_session

    app.dependency_overrides[get_usuario_actual] = lambda: admin_mock
    app.dependency_overrides[get_usuarios_uow] = lambda: mock_uow
    app.dependency_overrides[get_session] = override_get_session
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # Intenta revocar su propio rol ADMIN (usuario_id=1)
            resp = await ac.delete("/usuarios/1/roles/ADMIN")
            assert resp.status_code == status.HTTP_409_CONFLICT
            assert "no puede revocarse su propio rol ADMIN" in resp.json()["detail"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_autoproteccion_sistema_nunca_queda_sin_admins():
    """Valida que el sistema nunca quede sin administradores vigentes: 409 (RN-05)."""
    from app.core.database import get_session

    admin_mock = Usuario(
        id=1,
        email="admin1@example.com",
        nombre="Admin Uno",
        password_hash="hash",
        activo=True,
        debe_cambiar_password=False,
    )
    target_admin = Usuario(
        id=2,
        email="admin2@example.com",
        nombre="Admin Dos",
        password_hash="hash",
        activo=True,
        debe_cambiar_password=False,
    )
    mock_uow = MagicMock()
    mock_uow.usuarios = AsyncMock()
    mock_uow.usuarios.get_by_id.return_value = target_admin
    mock_uow.roles = AsyncMock()
    # Simular que solo queda 1 admin vigente
    mock_uow.roles.contar_admins_vigentes.return_value = 1

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = ["ADMIN"]
    mock_session = AsyncMock()
    mock_session.execute.return_value = mock_result

    async def override_get_session():
        yield mock_session

    app.dependency_overrides[get_usuario_actual] = lambda: admin_mock
    app.dependency_overrides[get_usuarios_uow] = lambda: mock_uow
    app.dependency_overrides[get_session] = override_get_session
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # Admin 1 intenta revocar al Admin 2 cuando solo queda 1 admin vigente
            resp = await ac.delete("/usuarios/2/roles/ADMIN")
            assert resp.status_code == status.HTTP_409_CONFLICT
            assert "nunca queda sin administradores vigentes" in resp.json()["detail"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_cambio_obligatorio_bloquea_rutas_protegidas():
    """Valida que usuario con debe_cambiar_password reciba 403 en rutas protegidas (RN-06)."""
    user_con_cambio_pendiente = Usuario(
        id=3,
        email="nuevo@example.com",
        nombre="Nuevo Personal",
        password_hash="hash",
        activo=True,
        debe_cambiar_password=True,
    )
    app.dependency_overrides[get_usuario_actual] = lambda: user_con_cambio_pendiente
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get("/usuarios/3/roles")
            assert resp.status_code == status.HTTP_403_FORBIDDEN
            assert "Debe cambiar su contraseña" in resp.json()["detail"]
    finally:
        app.dependency_overrides.clear()
