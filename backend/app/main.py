from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from fastapi import APIRouter, Depends, FastAPI
from app.core.config import Settings
from app.core.database import close_engine, create_engine_and_session_factory
from app.core.dependencies import verificar_cambio_password_obligatorio
from app.core.exceptions import setup_exception_handlers
from app.core.security import generate_dummy_hash
from app.modules.autores.router import (
    protected_router as autores_protected_router,
    public_router as autores_public_router,
)
from app.modules.clientes.router import router as clientes_router
from app.modules.editoriales.router import (
    protected_router as editoriales_protected_router,
    public_router as editoriales_public_router,
)
from app.modules.generos.router import (
    protected_router as generos_protected_router,
    public_router as generos_public_router,
)
from app.modules.health.router import router as health_router
from app.modules.libros.router import (
    protected_router as libros_protected_router,
    public_router as libros_public_router,
)
from app.modules.usuarios.admin_router import router as admin_router
from app.modules.usuarios.router import router as auth_router
from app.modules.ventas.router import router as ventas_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Ciclo de vida de la aplicación.
    
    Crea el motor asincrónico, la fábrica de sesiones y el hash ficticio
    dentro de app.state en lugar de crearlos al importar el módulo.
    Al detenerse, cierra el motor limpiamente con dispose().
    """
    settings = Settings()
    engine, session_factory = create_engine_and_session_factory(settings)
    
    # Pre-cálculo del hash ficticio para protección timing attack
    dummy_hash = generate_dummy_hash(rounds=settings.BCRYPT_ROUNDS)

    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = session_factory
    app.state.dummy_hash = dummy_hash

    try:
        yield
    finally:
        await close_engine(engine)


app = FastAPI(
    title="Librería API — Programación III",
    version="1.0.0",
    description="API asincrónica en capas con autenticación por cookie HttpOnly, roles en base, Unit of Work y stock de sólo agregado.",
    lifespan=lifespan,
)

# Ocultamiento de detalles internos y traducción de IntegrityError (RN-01, RN-15)
setup_exception_handlers(app)

# Dos grupos de rutas:
# 1. Grupo abierto: público, no exige sesión ni cambio de contraseña
api_abierta = APIRouter()
api_abierta.include_router(health_router)
api_abierta.include_router(auth_router)
api_abierta.include_router(clientes_router)
api_abierta.include_router(libros_public_router)
api_abierta.include_router(editoriales_public_router)
api_abierta.include_router(generos_public_router)
api_abierta.include_router(autores_public_router)
api_abierta.include_router(ventas_router)

# 2. Grupo protegido: rutas autenticadas que verifican cambio obligatorio de contraseña montado una sola vez
api_protegida = APIRouter(dependencies=[Depends(verificar_cambio_password_obligatorio)])
api_protegida.include_router(admin_router)
api_protegida.include_router(libros_protected_router)
api_protegida.include_router(editoriales_protected_router)
api_protegida.include_router(generos_protected_router)
api_protegida.include_router(autores_protected_router)

app.include_router(api_abierta)
app.include_router(api_protegida)
