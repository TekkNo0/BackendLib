import logging
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger("libreria_api")


def setup_exception_handlers(app: FastAPI) -> None:
    """Configura manejadores de excepción globales para ocultar detalles internos (RN-01, RN-15)."""

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
        logger.warning(
            "IntegrityError interceptado en %s: %s",
            request.url.path,
            str(exc.orig) if hasattr(exc, "orig") else str(exc),
        )
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": "Conflicto de integridad de datos: el registro ya existe o viola una restricción de clave única/foránea (RN-01)."
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": jsonable_encoder(exc.errors())},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Excepción no controlada en %s: %s", request.url.path, exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Error interno del servidor (RN-15)."},
        )
