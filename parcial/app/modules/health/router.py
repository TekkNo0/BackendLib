from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/live", status_code=status.HTTP_200_OK)
async def health_live() -> dict[str, str]:
    """Sonda de vida: no toca la base de datos."""
    return {"status": "live"}


@router.get("/ready", status_code=status.HTTP_200_OK)
async def health_ready(session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    """Sonda de preparación: ejecuta SELECT 1 y responde 503 si la base no está lista."""
    try:
        await session.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Base de datos no disponible: {exc}"
        ) from exc
