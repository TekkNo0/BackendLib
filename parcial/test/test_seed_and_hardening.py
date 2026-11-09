from unittest.mock import AsyncMock, MagicMock
from fastapi import FastAPI, status
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.exc import IntegrityError
from app.core.exceptions import setup_exception_handlers
from seed import run_seed


@pytest.mark.asyncio
async def test_seed_execution_and_idempotency():
    """Valida la ejecución idempotente de run_seed."""
    mock_session = AsyncMock()

    # Primera ejecución: base sin seed previo
    mock_result_empty = MagicMock()
    mock_result_empty.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result_empty

    await run_seed(mock_session)

    # Verifica que se hizo commit
    mock_session.commit.assert_called_once()
    # Verifica que se agregaron múltiples entidades
    assert mock_session.add.call_count > 10

    # Segunda ejecución: ya existe registro en evento_seguridad
    mock_session.reset_mock()
    mock_result_loaded = MagicMock()
    mock_result_loaded.scalar_one_or_none.return_value = MagicMock()
    mock_session.execute.return_value = mock_result_loaded

    await run_seed(mock_session)
    # No agrega nada ni vuelve a hacer commit
    mock_session.commit.assert_not_called()
    mock_session.add.assert_not_called()


@pytest.mark.asyncio
async def test_integrity_error_handler_returns_409_without_internals():
    """RN-01 y RN-15: IntegrityError debe traducirse a HTTP 409 sin exponer detalles SQL."""
    test_app = FastAPI()
    setup_exception_handlers(test_app)

    @test_app.get("/test-integrity-error")
    async def endpoint_con_error_integridad():
        raise IntegrityError(
            "INSERT INTO cliente...",
            params={},
            orig=Exception('duplicate key value violates unique constraint "uq_cliente_email"'),
        )

    transport = ASGITransport(app=test_app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/test-integrity-error")
        assert resp.status_code == status.HTTP_409_CONFLICT
        body = resp.json()
        assert "Conflicto de integridad" in body["detail"]
        # Garantía RN-15: Ningún detalle interno en la respuesta
        assert "uq_cliente_email" not in str(body)
        assert "INSERT INTO" not in str(body)
        assert "duplicate key" not in str(body)


@pytest.mark.asyncio
async def test_generic_exception_handler_returns_500_without_stacktrace():
    """RN-15: Excepciones no controladas deben responder 500 con mensaje genérico sin trazas."""
    test_app = FastAPI()
    setup_exception_handlers(test_app)

    @test_app.get("/test-generic-error")
    async def endpoint_con_error_inesperado():
        raise RuntimeError("Fallo crítico e inesperado en infraestructura interna")

    transport = ASGITransport(app=test_app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/test-generic-error")
        assert resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        body = resp.json()
        assert body["detail"] == "Error interno del servidor (RN-15)."
        assert "RuntimeError" not in str(body)
        assert "Fallo crítico" not in str(body)
