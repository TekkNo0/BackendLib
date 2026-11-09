from typing import Any
from fastapi import Depends, HTTPException, Request, status
import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.database import get_session
from app.core.security import decode_access_token
from app.modules.usuarios.unit_of_work import UsuariosUnitOfWork


def get_settings(request: Request) -> Settings:
    """Obtiene la configuración cargada en el estado de la aplicación."""
    return request.app.state.settings


def get_usuarios_uow(session: AsyncSession = Depends(get_session)) -> UsuariosUnitOfWork:
    """Construye e inyecta el Unit of Work del módulo usuarios con la sesión del request."""
    return UsuariosUnitOfWork(session=session)


def get_client_ip(request: Request) -> str:
    """Extrae la dirección IP del cliente desde el request."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


def get_token_payload(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """Lee y valida el token JWT desde la cookie HttpOnly access_token (Ejercicio 4)."""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado: falta cookie access_token",
        )
    try:
        payload = decode_access_token(
            token=token,
            secret_key=settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        ) from exc


def get_current_user_id(payload: dict[str, Any] = Depends(get_token_payload)) -> int:
    """Extrae el id de usuario (sub) desde el payload verificado."""
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: falta claim sub",
        )
    try:
        return int(sub)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: sub debe ser numérico",
        ) from exc


async def get_usuario_actual(
    payload: dict[str, Any] = Depends(get_token_payload),
    session: AsyncSession = Depends(get_session),
):
    """Obtiene el usuario autenticado desde la base de datos usando la misma sesión del request (Sección 6.7)."""
    from app.modules.usuarios.models import Usuario

    user_id = int(payload["sub"])
    usuario = await session.get(Usuario, user_id)
    if not usuario or not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no autenticado o inactivo",
        )
    return usuario


def requiere_rol(*roles_permitidos: str):
    """Dependencia que consulta los roles vigentes en la base de datos en cada petición (RN-04)."""
    async def rol_dependency(
        usuario=Depends(get_usuario_actual),
        session: AsyncSession = Depends(get_session),
    ):
        from app.modules.usuarios.repository import AsignacionRolRepository

        repo = AsignacionRolRepository(session)
        roles_vigentes = await repo.get_roles_vigentes(usuario.id)

        if not any(r in roles_vigentes for r in roles_permitidos):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No posee los permisos necesarios para realizar esta acción",
            )
        return usuario

    return rol_dependency


async def verificar_cambio_password_obligatorio(
    usuario=Depends(get_usuario_actual),
):
    """Bloquea el acceso a rutas protegidas si el usuario tiene un cambio de contraseña pendiente (RN-06)."""
    if usuario.debe_cambiar_password:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Debe cambiar su contraseña antes de continuar.",
        )
    return usuario
