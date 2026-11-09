from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException, status
import pytest
from httpx import ASGITransport, AsyncClient
from main import app
from app.core.database import get_session
from app.core.dependencies import get_usuario_actual
from app.modules.autores.models import Autor
from app.modules.editoriales.models import Editorial
from app.modules.generos.models import Genero
from app.modules.libros.models import Libro, LibroAutor
from app.modules.libros.schemas import (
    LibroCreateRequest,
    LibroUpdateRequest,
    ReponerStockRequest,
)
from app.modules.libros.service import LibroService
from app.modules.usuarios.models import Usuario
from app.modules.ventas.models import MovimientoStock


def test_schema_patch_blocks_stock_modification_422():
    """Caso C-13: PATCH a libro no permite modificar stock (debe responder 422)."""
    with pytest.raises(ValueError) as exc:
        LibroUpdateRequest.model_validate({"stock": 10})
    assert "El stock no puede modificarse por este endpoint" in str(exc.value)

    # Con otros campos pero incluyendo stock también debe fallar
    with pytest.raises(ValueError) as exc2:
        LibroUpdateRequest.model_validate({"titulo": "Nuevo Titulo", "stock": 5})
    assert "El stock no puede modificarse por este endpoint" in str(exc2.value)


def test_schema_libro_create_negative_stock_raises_422():
    """Valida que stock inicial negativo lance error de validación 422."""
    with pytest.raises(ValueError):
        LibroCreateRequest(
            isbn="978-987-0001-01-1",
            titulo="Libro Test",
            precio=Decimal("1500.00"),
            editorial_id=1,
            genero_id=1,
            autores_ids=[1],
            stock_inicial=-5,
        )


@pytest.mark.asyncio
async def test_crear_libro_con_stock_inicial_registra_movimiento():
    """Valida creación atómica de libro, autores y movimiento inicial (RN-09, RN-11)."""
    mock_session = AsyncMock()
    service = LibroService(mock_session)

    service.editorial_repo.get_by_id = AsyncMock(return_value=Editorial(id=1, nombre="Sudamericana"))
    service.genero_repo.get_by_id = AsyncMock(return_value=Genero(id=1, nombre="Novela"))
    service.autor_repo.get_by_ids = AsyncMock(
        return_value=[Autor(id=1, nombre="Julio Cortázar", nacionalidad="Argentina")]
    )
    service.libro_repo.get_vigente_by_isbn = AsyncMock(return_value=None)

    creado = Libro(
        id=1,
        isbn="978-987-0001-01-1",
        titulo="Rayuela",
        precio=Decimal("25000.00"),
        stock=10,
        editorial_id=1,
        genero_id=1,
    )
    creado.editorial = Editorial(id=1, nombre="Sudamericana")
    creado.genero = Genero(id=1, nombre="Novela")
    creado.autores_asociados = [
        LibroAutor(libro_id=1, autor_id=1, rol="autor", orden=1, autor=Autor(id=1, nombre="Julio Cortázar", nacionalidad="Argentina"))
    ]

    service.libro_repo.add = AsyncMock(return_value=creado)
    service.movimiento_repo.add = AsyncMock()
    service.libro_repo.get_detalle_vigente = AsyncMock(return_value=creado)

    req = LibroCreateRequest(
        isbn="978-987-0001-01-1",
        titulo="Rayuela",
        precio=Decimal("25000.00"),
        editorial_id=1,
        genero_id=1,
        autores_ids=[1],
        stock_inicial=10,
    )
    res = await service.crear_libro(req, usuario_id=1)

    assert res.id == 1
    assert res.stock == 10
    assert len(res.autores) == 1
    assert res.autores[0].nombre == "Julio Cortázar"
    service.movimiento_repo.add.assert_called_once()
    mov = service.movimiento_repo.add.call_args[0][0]
    assert mov.cantidad == 10
    assert mov.motivo == "Stock inicial"


@pytest.mark.asyncio
async def test_reponer_stock_incrementa_y_registra_movimiento():
    """Valida reposición atómica de stock registrando movimiento (RN-11)."""
    mock_session = AsyncMock()
    service = LibroService(mock_session)

    libro = Libro(
        id=1,
        isbn="978-987-0001-01-1",
        titulo="Rayuela",
        precio=Decimal("25000.00"),
        stock=5,
        editorial_id=1,
        genero_id=1,
        borrado_en=None,
    )
    libro.editorial = Editorial(id=1, nombre="Sudamericana")
    libro.genero = Genero(id=1, nombre="Novela")
    libro.autores_asociados = []

    service.libro_repo.get_detalle_any = AsyncMock(return_value=libro)
    service.libro_repo.update = AsyncMock()
    service.movimiento_repo.add = AsyncMock()
    service.libro_repo.get_detalle_vigente = AsyncMock(return_value=libro)

    req = ReponerStockRequest(cantidad=15, motivo="Reposición proveedor")
    res = await service.reponer_stock(libro_id=1, data=req, usuario_id=1)

    assert libro.stock == 20
    service.movimiento_repo.add.assert_called_once()
    mov = service.movimiento_repo.add.call_args[0][0]
    assert mov.cantidad == 15
    assert mov.motivo == "Reposición proveedor"


@pytest.mark.asyncio
async def test_reponer_stock_libro_borrado_responde_409():
    """Valida que intentar reponer stock sobre un libro borrado lógicamente responda 409 (RN-13)."""
    mock_session = AsyncMock()
    service = LibroService(mock_session)

    libro_borrado = Libro(
        id=1,
        isbn="978-987-0001-01-1",
        titulo="Descatalogado",
        precio=Decimal("1000.00"),
        stock=0,
        editorial_id=1,
        genero_id=1,
        borrado_en=datetime.now(timezone.utc),
    )
    service.libro_repo.get_detalle_any = AsyncMock(return_value=libro_borrado)

    req = ReponerStockRequest(cantidad=5, motivo="Intento inválido")
    with pytest.raises(HTTPException) as exc:
        await service.reponer_stock(libro_id=1, data=req, usuario_id=1)
    assert exc.value.status_code == status.HTTP_409_CONFLICT
    assert "descatalogado" in exc.value.detail


@pytest.mark.asyncio
async def test_borrado_logico_y_reuso_isbn():
    """Caso C-16: Borrado lógico responde 204 y permite reuso de ISBN en nueva alta."""
    mock_session = AsyncMock()
    service = LibroService(mock_session)

    libro_activo = Libro(
        id=1,
        isbn="978-987-0001-01-1",
        titulo="Edición Antigua",
        precio=Decimal("10000.00"),
        stock=2,
        editorial_id=1,
        genero_id=1,
        borrado_en=None,
    )
    service.libro_repo.get_detalle_any = AsyncMock(return_value=libro_activo)
    service.libro_repo.soft_delete = AsyncMock()

    # 1. DELETE responde 204 (sin retorno)
    await service.borrar_libro(libro_id=1)
    service.libro_repo.soft_delete.assert_called_once_with(libro_activo)

    # 2. Intentar borrar un libro ya descatalogado devuelve 404
    libro_ya_borrado = Libro(
        id=1,
        isbn="978-987-0001-01-1",
        titulo="Edición Antigua",
        precio=Decimal("10000.00"),
        stock=2,
        editorial_id=1,
        genero_id=1,
        borrado_en=datetime.now(timezone.utc),
    )
    service.libro_repo.get_detalle_any = AsyncMock(return_value=libro_ya_borrado)
    with pytest.raises(HTTPException) as exc_del:
        await service.borrar_libro(libro_id=1)
    assert exc_del.value.status_code == status.HTTP_404_NOT_FOUND

    # 3. Reuso de ISBN: alta con el mismo ISBN tras la baja no colisiona (RN-01, RN-13)
    service.editorial_repo.get_by_id = AsyncMock(return_value=Editorial(id=1, nombre="Sudamericana"))
    service.genero_repo.get_by_id = AsyncMock(return_value=Genero(id=1, nombre="Novela"))
    service.autor_repo.get_by_ids = AsyncMock(return_value=[Autor(id=1, nombre="Cortázar", nacionalidad="Arg")])
    service.libro_repo.get_vigente_by_isbn = AsyncMock(return_value=None)  # El anterior borrado no es vigente!

    nuevo_libro = Libro(
        id=2,
        isbn="978-987-0001-01-1",
        titulo="Edición Nueva",
        precio=Decimal("20000.00"),
        stock=5,
        editorial_id=1,
        genero_id=1,
    )
    nuevo_libro.editorial = Editorial(id=1, nombre="Sudamericana")
    nuevo_libro.genero = Genero(id=1, nombre="Novela")
    nuevo_libro.autores_asociados = []

    service.libro_repo.add = AsyncMock(return_value=nuevo_libro)
    service.movimiento_repo.add = AsyncMock()
    service.libro_repo.get_detalle_vigente = AsyncMock(return_value=nuevo_libro)

    req_reuso = LibroCreateRequest(
        isbn="978-987-0001-01-1",
        titulo="Edición Nueva",
        precio=Decimal("20000.00"),
        editorial_id=1,
        genero_id=1,
        autores_ids=[1],
        stock_inicial=5,
    )
    res_nuevo = await service.crear_libro(req_reuso, usuario_id=1)
    assert res_nuevo.id == 2
    assert res_nuevo.isbn == "978-987-0001-01-1"


@pytest.mark.asyncio
async def test_http_endpoint_patch_stock_returns_422():
    """Caso C-13 vía cliente HTTP: PATCH /libros/{id} con campo stock debe devolver HTTP 422."""
    admin_mock = Usuario(
        id=1,
        email="admin@example.com",
        nombre="Admin",
        password_hash="hash",
        activo=True,
        debe_cambiar_password=False,
    )
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = ["ADMIN"]
    mock_session.execute.return_value = mock_result

    async def override_get_session():
        yield mock_session

    app.dependency_overrides[get_usuario_actual] = lambda: admin_mock
    app.dependency_overrides[get_session] = override_get_session

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.patch("/libros/1", json={"stock": 50})
            assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            body = resp.json()
            assert "stock" in str(body).lower()
    finally:
        app.dependency_overrides.clear()
