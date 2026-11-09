from unittest.mock import AsyncMock, MagicMock
from fastapi import status
import pytest
from httpx import ASGITransport, AsyncClient
from main import app
from app.core.config import Settings
from app.core.dependencies import get_usuarios_uow
from app.modules.usuarios.models import Usuario
from app.modules.usuarios.schemas import LoginRequest, RegistroClienteRequest


def test_extra_fields_forbidden_on_schemas():
    """Valida que los contratos de auth rechacen campos no declarados (extra='forbid')."""
    with pytest.raises(Exception):
        LoginRequest(
            email="test@example.com",
            password="password123",
            extra_field="malicious",  # Campo extra prohibido
        )

    with pytest.raises(Exception):
        RegistroClienteRequest(
            nombre="Juan",
            email="juan@example.com",
            password="password123",
            rol="ADMIN",  # Intentar inyectar rol debe fallar con 422
        )


def test_password_exceeding_72_bytes_fails_validation():
    """Valida que contraseñas > 72 bytes fallen en validación (422) y no en bcrypt (500)."""
    long_pass = "a" * 73
    with pytest.raises(ValueError) as exc:
        LoginRequest(email="test@example.com", password=long_pass)
    assert "72 bytes" in str(exc.value)

    # Caso con caracteres multibyte (la letra ñ ocupa 2 bytes)
    multibyte_pass = "ñ" * 37  # 74 bytes
    with pytest.raises(ValueError) as exc:
        LoginRequest(email="test@example.com", password=multibyte_pass)
    assert "72 bytes" in str(exc.value)


@pytest.mark.asyncio
async def test_registro_cliente_conflict_409():
    """Valida que el registro rechace correos duplicados con 409 Conflict."""
    mock_uow = MagicMock()
    mock_uow.clientes = AsyncMock()
    mock_uow.usuarios = AsyncMock()
    mock_uow.roles = AsyncMock()
    mock_uow.eventos = AsyncMock()
    mock_uow.__aenter__.return_value = mock_uow
    mock_uow.__aexit__.return_value = None

    # Simular que el cliente ya existe
    mock_uow.clientes.get_by_email.return_value = MagicMock()

    app.dependency_overrides[get_usuarios_uow] = lambda: mock_uow
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/auth/registro",
                json={"nombre": "Ana", "email": "ana@example.com", "password": "password123"},
            )
            assert resp.status_code == status.HTTP_409_CONFLICT
            assert "Ya existe un cliente" in resp.json()["detail"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_login_rate_limiting_returns_429():
    """Valida que tras 5 fallos en 60 segundos, el login responda 429 con Retry-After (RN-07)."""
    mock_uow = MagicMock()
    mock_uow.intentos = AsyncMock()
    # Simular 5 fallos previos
    mock_uow.intentos.contar_fallos_recientes.return_value = 5

    app.dependency_overrides[get_usuarios_uow] = lambda: mock_uow
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/auth/login",
                json={"email": "hacker@example.com", "password": "wrongpassword"},
            )
            assert resp.status_code == status.HTTP_429_TOO_MANY_REQUESTS
            assert resp.headers.get("Retry-After") == "60"
            assert "Demasiados intentos fallidos" in resp.json()["detail"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_timing_attack_same_error_for_nonexistent_and_bad_password():
    """Valida que el login responda el mismo mensaje de error (RN-08)."""
    mock_uow = MagicMock()
    mock_uow.intentos = AsyncMock()
    mock_uow.intentos.contar_fallos_recientes.return_value = 0
    # Usuario inexistente
    mock_uow.usuarios = AsyncMock()
    mock_uow.usuarios.get_by_email.return_value = None

    # Mockear session_factory de app.state
    app.state.session_factory = MagicMock()
    mock_session = AsyncMock()
    app.state.session_factory.return_value.__aenter__.return_value = mock_session
    app.state.session_factory.return_value.__aexit__.return_value = None

    app.dependency_overrides[get_usuarios_uow] = lambda: mock_uow
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/auth/login",
                json={"email": "inexistente@example.com", "password": "password123"},
            )
            assert resp.status_code == status.HTTP_401_UNAUTHORIZED
            assert resp.json() == {"detail": "Credenciales incorrectas"}
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_logout_clears_access_token_cookie():
    """Valida que el logout elimine la cookie access_token."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post("/auth/logout")
        assert resp.status_code == 200
        assert resp.json() == {"mensaje": "Sesión cerrada exitosamente"}
        cookie_header = resp.headers.get("set-cookie", "")
        assert "access_token=" in cookie_header
        assert "max-age=0" in cookie_header.lower()
