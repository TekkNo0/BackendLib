from fastapi import APIRouter, Depends, status

from app.core.config import Settings
from app.core.dependencies import (
    get_settings,
    get_usuarios_uow,
    requiere_rol,
)
from app.core.paginacion import PaginationParams, PaginatedResponse, paginate
from app.modules.usuarios.models import Usuario
from app.modules.usuarios.schemas import (
    AltaPersonalRequest,
    AsignacionRolResponse,
    AsignarRolRequest,
    EventoSeguridadResponse,
    UsuarioResponse,
)
from app.modules.usuarios.service import AuthService
from app.modules.usuarios.unit_of_work import UsuariosUnitOfWork

router = APIRouter(tags=["Administración de Usuarios y Roles"])
auth_service = AuthService()


@router.post(
    "/usuarios",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Alta de personal con contraseña provisoria",
)
async def alta_personal(
    req: AltaPersonalRequest,
    admin: Usuario = Depends(requiere_rol("ADMIN")),
    uow: UsuariosUnitOfWork = Depends(get_usuarios_uow),
    settings: Settings = Depends(get_settings),
) -> UsuarioResponse:
    """Da de alta a un miembro del personal con debe_cambiar_password activado (Solo ADMIN)."""
    usuario = await auth_service.alta_personal(
        uow=uow,
        admin_email=admin.email,
        nombre=req.nombre,
        email=req.email,
        password_provisoria=req.password_provisoria,
        rounds=settings.BCRYPT_ROUNDS,
    )
    return UsuarioResponse(
        id=usuario.id,  # type: ignore
        email=usuario.email,
        nombre=usuario.nombre,
        activo=usuario.activo,
        debe_cambiar_password=usuario.debe_cambiar_password,
    )


@router.get(
    "/usuarios/{usuario_id}/roles",
    response_model=list[AsignacionRolResponse],
    status_code=status.HTTP_200_OK,
    summary="Historial de roles de un usuario",
)
async def ver_roles(
    usuario_id: int,
    admin: Usuario = Depends(requiere_rol("ADMIN")),
    uow: UsuariosUnitOfWork = Depends(get_usuarios_uow),
) -> list[AsignacionRolResponse]:
    """Lista las asignaciones de rol (activas, vencidas o revocadas) de un usuario (Solo ADMIN)."""
    roles = await auth_service.listar_roles(uow=uow, usuario_id=usuario_id)
    return [
        AsignacionRolResponse(
            id=r.id,  # type: ignore
            usuario_id=r.usuario_id,
            rol=r.rol,
            desde=r.desde.isoformat(),
            vence_en=r.vence_en.isoformat() if r.vence_en else None,
            revocada_en=r.revocada_en.isoformat() if r.revocada_en else None,
            otorgada_por=r.otorgada_por,
        )
        for r in roles
    ]


@router.post(
    "/usuarios/{usuario_id}/roles",
    response_model=AsignacionRolResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Asignar rol a un usuario",
)
async def asignar_rol(
    usuario_id: int,
    req: AsignarRolRequest,
    admin: Usuario = Depends(requiere_rol("ADMIN")),
    uow: UsuariosUnitOfWork = Depends(get_usuarios_uow),
) -> AsignacionRolResponse:
    """Asigna un rol con vencimiento opcional en el futuro (RN-03, RN-16, Solo ADMIN)."""
    asig = await auth_service.asignar_rol(
        uow=uow,
        admin_id=admin.id,  # type: ignore
        admin_email=admin.email,
        usuario_id=usuario_id,
        rol=req.rol,
        vence_en_iso=req.vence_en,
    )
    return AsignacionRolResponse(
        id=asig.id,  # type: ignore
        usuario_id=asig.usuario_id,
        rol=asig.rol,
        desde=asig.desde.isoformat(),
        vence_en=asig.vence_en.isoformat() if asig.vence_en else None,
        revocada_en=asig.revocada_en.isoformat() if asig.revocada_en else None,
        otorgada_por=asig.otorgada_por,
    )


@router.delete(
    "/usuarios/{usuario_id}/roles/{rol}",
    status_code=status.HTTP_200_OK,
    summary="Revocar un rol asignado",
)
async def revocar_rol(
    usuario_id: int,
    rol: str,
    admin: Usuario = Depends(requiere_rol("ADMIN")),
    uow: UsuariosUnitOfWork = Depends(get_usuarios_uow),
) -> dict[str, str]:
    """Revoca una asignación de rol abierta con autoprotección (RN-05, Solo ADMIN)."""
    await auth_service.revocar_rol(
        uow=uow,
        admin_id=admin.id,  # type: ignore
        admin_email=admin.email,
        usuario_id=usuario_id,
        rol=rol,
    )
    return {"mensaje": f"Rol {rol.upper()} revocado exitosamente"}


@router.get(
    "/eventos",
    response_model=PaginatedResponse[EventoSeguridadResponse],
    status_code=status.HTTP_200_OK,
    summary="Historial de auditoría de seguridad",
)
async def listar_eventos(
    pagination: PaginationParams = Depends(),
    admin: Usuario = Depends(requiere_rol("ADMIN")),
    uow: UsuariosUnitOfWork = Depends(get_usuarios_uow),
) -> PaginatedResponse[EventoSeguridadResponse]:
    """Consulta paginada del log de seguridad evento_seguridad (RN-16, Solo ADMIN)."""
    total = await uow.eventos.count()
    items = await uow.eventos.get_all(offset=pagination.offset, limit=pagination.limit)
    response_items = [
        EventoSeguridadResponse(
            id=e.id,  # type: ignore
            cuando=e.cuando.isoformat(),
            actor=e.actor,
            accion=e.accion,
        )
        for e in items
    ]
    return paginate(items=response_items, total=total, params=pagination)
