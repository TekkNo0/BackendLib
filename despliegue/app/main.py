import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from decimal import Decimal
from typing import Any
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.config import Settings
from app.core.database import close_engine, create_engine_and_session_factory, get_session
from app.models import Autor, Cliente, Editorial, Genero, Libro, RenglonVenta, Venta


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = Settings()
    engine, session_factory = create_engine_and_session_factory(settings)
    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = session_factory
    try:
        yield
    finally:
        await close_engine(engine)


app = FastAPI(
    title="Librería API — TP Capítulos 1 a 4",
    version="1.0.0",
    lifespan=lifespan,
)


# ------------------------------------------------------------------------------
# Health endpoints
# ------------------------------------------------------------------------------
@app.get("/health/live")
async def health_live() -> dict[str, str]:
    return {"status": "live"}


@app.get("/health/ready")
async def health_ready(session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    try:
        await session.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Base de datos no disponible: {exc}",
        ) from exc


# ------------------------------------------------------------------------------
# Catálogo y entidades
# ------------------------------------------------------------------------------
@app.get("/libros")
@app.get("/libros/")
async def listar_libros(session: AsyncSession = Depends(get_session)) -> list[dict[str, Any]]:
    stmt = select(Libro).order_by(Libro.id)
    items = (await session.execute(stmt)).scalars().all()
    return [
        {
            "id": l.id,
            "isbn": l.isbn,
            "titulo": l.titulo,
            "precio": float(l.precio),
            "stock": l.stock,
            "editorial_id": l.editorial_id,
            "genero_id": l.genero_id,
        }
        for l in items
    ]


@app.get("/libros/{id}")
async def obtener_libro(id: int, session: AsyncSession = Depends(get_session)) -> dict[str, Any]:
    libro = await session.get(Libro, id)
    if not libro:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    return {
        "id": libro.id,
        "isbn": libro.isbn,
        "titulo": libro.titulo,
        "precio": float(libro.precio),
        "stock": libro.stock,
        "editorial_id": libro.editorial_id,
        "genero_id": libro.genero_id,
    }


@app.get("/editoriales")
@app.get("/editoriales/")
async def listar_editoriales(session: AsyncSession = Depends(get_session)):
    stmt = select(Editorial).order_by(Editorial.id)
    return (await session.execute(stmt)).scalars().all()


@app.get("/generos")
@app.get("/generos/")
async def listar_generos(session: AsyncSession = Depends(get_session)):
    stmt = select(Genero).order_by(Genero.id)
    return (await session.execute(stmt)).scalars().all()


@app.get("/autores")
@app.get("/autores/")
async def listar_autores(session: AsyncSession = Depends(get_session)):
    stmt = select(Autor).order_by(Autor.id)
    return (await session.execute(stmt)).scalars().all()


@app.get("/clientes")
@app.get("/clientes/")
async def listar_clientes(session: AsyncSession = Depends(get_session)):
    stmt = select(Cliente).order_by(Cliente.id)
    return (await session.execute(stmt)).scalars().all()


# ------------------------------------------------------------------------------
# Ventas
# ------------------------------------------------------------------------------
class RenglonIn(BaseModel):
    libro_id: int
    cantidad: int = Field(gt=0)


class VentaIn(BaseModel):
    cliente_id: int
    renglones: list[RenglonIn]


async def simular_despacho_comprobante(venta_id: int) -> None:
    await asyncio.sleep(0.5)
    print(f"[BACKGROUND] Comprobante de venta #{venta_id} despachado al cliente")


@app.post("/ventas", status_code=status.HTTP_201_CREATED)
@app.post("/ventas/", status_code=status.HTTP_201_CREATED)
async def crear_venta(
    data: VentaIn,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    cliente = await session.get(Cliente, data.cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    total = Decimal("0.00")
    renglones_model = []

    for item in data.renglones:
        libro = await session.get(Libro, item.libro_id)
        if not libro:
            raise HTTPException(status_code=404, detail=f"Libro {item.libro_id} no encontrado")
        if libro.stock < item.cantidad:
            raise HTTPException(
                status_code=409,
                detail=f"Stock insuficiente para libro {libro.titulo}",
            )
        libro.stock -= item.cantidad
        subtotal = libro.precio * item.cantidad
        total += subtotal
        renglones_model.append((libro, item.cantidad, libro.precio))

    venta = Venta(cliente_id=data.cliente_id, total=total)
    session.add(venta)
    await session.flush()

    for libro, cant, pu in renglones_model:
        r = RenglonVenta(
            venta_id=venta.id,
            libro_id=libro.id,
            cantidad=cant,
            precio_unitario=pu,
        )
        session.add(r)

    await session.commit()
    background_tasks.add_task(simular_despacho_comprobante, venta.id)

    return {
        "id": venta.id,
        "cliente_id": venta.cliente_id,
        "fecha": venta.fecha.isoformat(),
        "total": float(venta.total),
        "renglones": [
            {
                "libro_id": r.libro_id,
                "cantidad": r.cantidad,
                "precio_unitario": float(r.precio_unitario),
            }
            for _, r in enumerate(session.new)
            if isinstance(r, RenglonVenta)
        ],
    }
