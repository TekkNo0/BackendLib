import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException, status
import pytest
from httpx import ASGITransport, AsyncClient
from main import app
from app.core.database import get_session
from app.core.dependencies import get_usuario_actual
from app.modules.clientes.models import Cliente
from app.modules.libros.models import Libro
from app.modules.usuarios.models import Usuario
from app.modules.ventas.models import MovimientoStock, RenglonVenta, Venta
from app.modules.ventas.router import simular_despacho
from app.modules.ventas.schemas import (
    RenglonVentaCreateRequest,
    VentaCreateRequest,
)
from app.modules.ventas.service import VentaService


def test_schema_validates_min_renglones_and_no_duplicates():
    """Valida que una venta exija al menos un renglón y no permita libros repetidos (RN-09)."""
    # 1. Renglones vacíos falla validación
    with pytest.raises(ValueError):
        VentaCreateRequest(cliente_id=1, renglones=[])

    # 2. Renglones con el mismo libro_id repetido falla validación
    with pytest.raises(ValueError) as exc:
        VentaCreateRequest(
            cliente_id=1,
            renglones=[
                RenglonVentaCreateRequest(libro_id=1, cantidad=2),
                RenglonVentaCreateRequest(libro_id=1, cantidad=1),
            ],
        )
    assert "No se permiten libros repetidos" in str(exc.value)


@pytest.mark.asyncio
async def test_crear_venta_exitosa_calcula_total_y_descuenta_stock():
    """Valida creación atómica de venta, copia de precios, total y movimientos de salida (RN-09, RN-10)."""
    mock_session = AsyncMock()
    service = VentaService(mock_session)

    cliente = Cliente(id=1, nombre="Lucía Fernández", email="lucia@example.com")
    service.cliente_repo.get_by_id = AsyncMock(return_value=cliente)

    libro1 = Libro(
        id=1,
        isbn="978-987-0001-01-1",
        titulo="Rayuela",
        precio=Decimal("25000.00"),
        stock=10,
        editorial_id=1,
        genero_id=1,
    )
    libro2 = Libro(
        id=2,
        isbn="978-987-0001-02-2",
        titulo="Ficciones",
        precio=Decimal("22000.00"),
        stock=8,
        editorial_id=1,
        genero_id=1,
    )

    def mock_get_libro(libro_id: int):
        if libro_id == 1:
            return libro1
        if libro_id == 2:
            return libro2
        return None

    service.libro_repo.get_detalle_vigente = AsyncMock(side_effect=mock_get_libro)
    service.libro_repo.update = AsyncMock()
    service.movimiento_repo.add = AsyncMock()

    venta_mock = Venta(id=1, cliente_id=1, total=Decimal("69000.00"))
    service.venta_repo.add = AsyncMock(return_value=venta_mock)
    service.venta_repo.update = AsyncMock()

    # Mock venta_cargada con relaciones
    venta_mock.cliente = cliente
    r1 = RenglonVenta(id=1, venta_id=1, libro_id=1, cantidad=1, precio_unitario=Decimal("25000.00"))
    r1.libro = libro1
    r2 = RenglonVenta(id=2, venta_id=1, libro_id=2, cantidad=2, precio_unitario=Decimal("22000.00"))
    r2.libro = libro2
    venta_mock.renglones = [r1, r2]

    service.venta_repo.get_detalle = AsyncMock(return_value=venta_mock)

    req = VentaCreateRequest(
        cliente_id=1,
        renglones=[
            RenglonVentaCreateRequest(libro_id=1, cantidad=1),
            RenglonVentaCreateRequest(libro_id=2, cantidad=2),
        ],
    )

    res = await service.crear_venta(req, usuario_id=99)

    assert res.id == 1
    # 25000 + 2 * 22000 = 69000
    assert res.total == Decimal("69000.00")
    assert len(res.renglones) == 2
    # Stock descontado
    assert libro1.stock == 9
    assert libro2.stock == 6
    # 2 movimientos de stock de salida registrados
    assert service.movimiento_repo.add.call_count == 2
    calls = service.movimiento_repo.add.call_args_list
    mov1 = calls[0][0][0]
    mov2 = calls[1][0][0]
    assert mov1.cantidad == -1
    assert mov2.cantidad == -2


@pytest.mark.asyncio
async def test_rollback_atomico_stock_insuficiente_caso_c15():
    """Caso C-15: Rollback atómico ante stock insuficiente (RN-10)."""
    mock_session = AsyncMock()
    service = VentaService(mock_session)

    cliente = Cliente(id=1, nombre="Lucía", email="lucia@example.com")
    service.cliente_repo.get_by_id = AsyncMock(return_value=cliente)

    libro_ok = Libro(
        id=1,
        isbn="978-987-0001-01-1",
        titulo="Rayuela",
        precio=Decimal("25000.00"),
        stock=5,
        editorial_id=1,
        genero_id=1,
    )
    libro_sin_stock = Libro(
        id=2,
        isbn="978-987-0001-02-2",
        titulo="Libro Escaso",
        precio=Decimal("10000.00"),
        stock=1,
        editorial_id=1,
        genero_id=1,
    )

    def mock_get_libro(libro_id: int):
        if libro_id == 1:
            return libro_ok
        if libro_id == 2:
            return libro_sin_stock
        return None

    service.libro_repo.get_detalle_vigente = AsyncMock(side_effect=mock_get_libro)
    service.venta_repo.add = AsyncMock()
    service.movimiento_repo.add = AsyncMock()

    # Solicitamos 3 ejemplares del libro 2 que sólo tiene stock 1
    req = VentaCreateRequest(
        cliente_id=1,
        renglones=[
            RenglonVentaCreateRequest(libro_id=1, cantidad=2),
            RenglonVentaCreateRequest(libro_id=2, cantidad=3),
        ],
    )

    with pytest.raises(HTTPException) as exc:
        await service.crear_venta(req, usuario_id=99)

    assert exc.value.status_code == status.HTTP_409_CONFLICT
    assert "Stock insuficiente" in exc.value.detail
    # La transacción no agregó venta ni movimientos
    service.venta_repo.add.assert_not_called()
    service.movimiento_repo.add.assert_not_called()
    # El stock del libro disponible no fue afectado
    assert libro_ok.stock == 5


@pytest.mark.asyncio
async def test_aislamiento_cliente_mis_ventas_y_403_venta_ajena_caso_c11_c12():
    """Casos C-11 y C-12: Aislamiento de ventas por cliente (RN-14)."""
    mock_session = AsyncMock()
    service = VentaService(mock_session)

    usuario_cliente = Usuario(
        id=10,
        email="ana@example.com",
        nombre="Ana Paz",
        password_hash="hash",
        activo=True,
        debe_cambiar_password=False,
    )
    cliente_ana = Cliente(id=1, nombre="Ana Paz", email="ana@example.com", usuario_id=10)
    service.cliente_repo.get_by_usuario_id = AsyncMock(return_value=cliente_ana)

    venta_propia = Venta(id=100, cliente_id=1, total=Decimal("5000.00"))
    venta_propia.cliente = cliente_ana
    venta_propia.renglones = []

    venta_ajena = Venta(id=200, cliente_id=2, total=Decimal("9999.00"))
    cliente_tomas = Cliente(id=2, nombre="Tomás", email="tomas@example.com")
    venta_ajena.cliente = cliente_tomas
    venta_ajena.renglones = []

    # 1. Caso C-11: Ana consulta su propia venta -> 200 OK
    service.venta_repo.get_detalle = AsyncMock(return_value=venta_propia)
    res_propia = await service.obtener_venta(
        venta_id=100, usuario=usuario_cliente, roles_vigentes=["CLIENTE"]
    )
    assert res_propia.id == 100

    # 2. Caso C-12: Ana intenta consultar venta ajena -> 403 Forbidden (RN-14)
    service.venta_repo.get_detalle = AsyncMock(return_value=venta_ajena)
    with pytest.raises(HTTPException) as exc:
        await service.obtener_venta(
            venta_id=200, usuario=usuario_cliente, roles_vigentes=["CLIENTE"]
        )
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN
    assert "No posee permisos" in exc.value.detail

    # 3. Un ADMIN o VENDEDOR sí puede ver la venta ajena sin restricción
    usuario_admin = Usuario(
        id=1,
        email="admin@example.com",
        nombre="Admin",
        password_hash="hash",
        activo=True,
        debe_cambiar_password=False,
    )
    res_admin = await service.obtener_venta(
        venta_id=200, usuario=usuario_admin, roles_vigentes=["ADMIN"]
    )
    assert res_admin.id == 200


@pytest.mark.asyncio
async def test_simular_despacho_background_task():
    """Valida la ejecución asincrónica de la tarea en segundo plano."""
    # Ejecuta sin elevar excepciones
    await simular_despacho(venta_id=123, cliente_email="test@example.com")
