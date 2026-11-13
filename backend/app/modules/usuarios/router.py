from typing import Any
from fastapi import APIRouter, Depends, Request, Response, status

from app.core.config import Settings
from app.core.dependencies import (
    get_client_ip,
    get_current_user_id,
    get_settings,
    get_token_payload,
    get_usuarios_uow,
)
from app.modules.usuarios.schemas import (
    AuthYoResponse,
    CambiarPasswordRequest,
    LoginRequest,
    LoginResponse,
    RegistroClienteRequest,
    UsuarioResponse,
)
from app.modules.usuarios.service import AuthService
from app.modules.usuarios.unit_of_work import UsuariosUnitOfWork

router = APIRouter(prefix="/auth", tags=["Autenticación"])
auth_service = AuthService()


@router.post(
    "/registro",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Auto-registro de cliente",
)
async def registro(
    req: RegistroClienteRequest,
    uow: UsuariosUnitOfWork = Depends(get_usuarios_uow),
    settings: Settings = Depends(get_settings),
) -> UsuarioResponse:
    """Auto-registro atómico de cliente (RN-02).
    
    Crea el usuario, su rol CLIENTE y su ficha de cliente en una sola transacción.
    Si ya existe un cliente o usuario con ese correo, responde 409 Conflict.
    """
    usuario = await auth_service.registrar_cliente(
        uow=uow,
        req=req,
        rounds=settings.BCRYPT_ROUNDS,
    )
    return UsuarioResponse(
        id=usuario.id,  # type: ignore
        email=usuario.email,
        nombre=usuario.nombre,
        activo=usuario.activo,
        debe_cambiar_password=usuario.debe_cambiar_password,
    )


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Inicio de sesión tradicional con cookie HttpOnly",
)
async def login(
    req: LoginRequest,
    request: Request,
    response: Response,
    uow: UsuariosUnitOfWork = Depends(get_usuarios_uow),
    settings: Settings = Depends(get_settings),
    ip: str = Depends(get_client_ip),
) -> LoginResponse:
    """Inicia sesión, evalúa rate limit (RN-07) y coloca el token JWT en cookie HttpOnly (Ejercicio 4)."""
    token, login_res = await auth_service.login(
        uow=uow,
        session_factory=request.app.state.session_factory,
        req=req,
        ip=ip,
        dummy_hash=request.app.state.dummy_hash,
        secret_key=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
        expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )

    # El token viaja EXCLUSIVAMENTE en la cookie access_token con HttpOnly
    response.set_cookie(
        key="access_token",
        value=token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
        path="/",
    )
    return login_res


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Cierre de sesión",
)
async def logout(response: Response) -> dict[str, str]:
    """Cierra la sesión borrando la cookie access_token."""
    response.delete_cookie(
        key="access_token",
        path="/",
        httponly=True,
        samesite="lax",
    )
    return {"mensaje": "Sesión cerrada exitosamente"}


@router.get(
    "/yo",
    response_model=AuthYoResponse,
    status_code=status.HTTP_200_OK,
    summary="Información de la sesión actual",
)
async def yo(
    user_id: int = Depends(get_current_user_id),
    payload: dict[str, Any] = Depends(get_token_payload),
    uow: UsuariosUnitOfWork = Depends(get_usuarios_uow),
) -> AuthYoResponse:
    """Devuelve el usuario actual, sus roles vigentes en la base y los informados por el token."""
    token_roles = payload.get("roles", [])
    return await auth_service.get_yo(
        uow=uow,
        usuario_id=user_id,
        token_roles=token_roles,
    )


@router.post(
    "/cambiar-password",
    status_code=status.HTTP_200_OK,
    summary="Cambio obligatorio o voluntario de contraseña",
)
async def cambiar_password(
    req: CambiarPasswordRequest,
    user_id: int = Depends(get_current_user_id),
    uow: UsuariosUnitOfWork = Depends(get_usuarios_uow),
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    """Actualiza la contraseña, resetea la bandera debe_cambiar_password y audita en evento_seguridad."""
    return await auth_service.cambiar_password(
        uow=uow,
        usuario_id=user_id,
        req=req,
        rounds=settings.BCRYPT_ROUNDS,
    )
