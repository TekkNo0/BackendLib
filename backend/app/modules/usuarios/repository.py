from datetime import datetime, timedelta, timezone
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from app.core.repository import BaseRepository
from app.modules.usuarios.models import AsignacionRol, EventoSeguridad, IntentoAcceso, Usuario


class UsuarioRepository(BaseRepository[Usuario]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=Usuario)

    async def get_by_email(self, email: str) -> Usuario | None:
        """Obtiene un usuario por su correo electrónico con carga anticipada de sus asignaciones de rol."""
        stmt = (
            select(Usuario)
            .where(Usuario.email == email)
            .options(selectinload(Usuario.asignaciones))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_with_roles(self, usuario_id: int) -> Usuario | None:
        stmt = (
            select(Usuario)
            .where(Usuario.id == usuario_id)
            .options(selectinload(Usuario.asignaciones))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class AsignacionRolRepository(BaseRepository[AsignacionRol]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=AsignacionRol)

    async def get_roles_vigentes(self, usuario_id: int) -> list[str]:
        """Consulta directamente en base los roles no revocados y no vencidos del usuario (RN-04)."""
        now = datetime.now(timezone.utc)
        stmt = (
            select(AsignacionRol.rol)
            .where(
                AsignacionRol.usuario_id == usuario_id,
                AsignacionRol.revocada_en.is_(None),
                or_(AsignacionRol.vence_en.is_(None), AsignacionRol.vence_en > now),
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_asignacion_abierta(self, usuario_id: int, rol: str) -> AsignacionRol | None:
        """Obtiene una asignación abierta para un rol determinado si existe."""
        stmt = (
            select(AsignacionRol)
            .where(
                AsignacionRol.usuario_id == usuario_id,
                AsignacionRol.rol == rol,
                AsignacionRol.revocada_en.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_roles_por_usuario(self, usuario_id: int) -> list[AsignacionRol]:
        """Obtiene todo el historial de roles (activos, revocados o vencidos) de un usuario."""
        stmt = (
            select(AsignacionRol)
            .where(AsignacionRol.usuario_id == usuario_id)
            .order_by(AsignacionRol.desde.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def contar_admins_vigentes(self) -> int:
        """Cuenta la cantidad de administradores actualmente vigentes (RN-05)."""
        now = datetime.now(timezone.utc)
        stmt = (
            select(func.count())
            .select_from(AsignacionRol)
            .where(
                AsignacionRol.rol == "ADMIN",
                AsignacionRol.revocada_en.is_(None),
                or_(AsignacionRol.vence_en.is_(None), AsignacionRol.vence_en > now),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def revocar_rol(self, usuario_id: int, rol: str) -> AsignacionRol | None:
        """Revoca la asignación abierta marcando revocada_en sin borrar la fila."""
        asignacion = await self.get_asignacion_abierta(usuario_id, rol)
        if asignacion:
            asignacion.revocada_en = datetime.now(timezone.utc)
            await self.session.flush()
        return asignacion


class IntentoAccesoRepository(BaseRepository[IntentoAcceso]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=IntentoAcceso)

    async def contar_fallos_recientes(self, email: str, ip: str, ventana_segundos: int = 60) -> int:
        """Cuenta los intentos fallidos recientes para el par (email, ip) posteriores al último login exitoso (RN-07)."""
        now = datetime.now(timezone.utc)
        corte = now - timedelta(seconds=ventana_segundos)

        # 1. Buscar último login exitoso para este par (email, ip)
        stmt_ultimo_exito = (
            select(func.max(IntentoAcceso.cuando))
            .where(
                IntentoAcceso.email == email,
                IntentoAcceso.ip == ip,
                IntentoAcceso.exito.is_(True),
            )
        )
        res_exito = await self.session.execute(stmt_ultimo_exito)
        ultimo_exito = res_exito.scalar_one_or_none()

        # 2. Contar fallos dentro de la ventana de tiempo y posteriores al último éxito
        stmt_fallos = (
            select(func.count())
            .select_from(IntentoAcceso)
            .where(
                IntentoAcceso.email == email,
                IntentoAcceso.ip == ip,
                IntentoAcceso.exito.is_(False),
                IntentoAcceso.cuando >= corte,
            )
        )
        if ultimo_exito is not None:
            stmt_fallos = stmt_fallos.where(IntentoAcceso.cuando > ultimo_exito)

        res_fallos = await self.session.execute(stmt_fallos)
        return res_fallos.scalar_one()


# ==============================================================================
# REGISTRO DE INTENTO DE ACCESO EN SESIÓN INDEPENDIENTE (Ejercicio 7 / Sección 6.8.1)
#
# 1. QUÉ HACE DISTINTO:
#    Esta función abre una sesión y una transacción propias e independientes a través
#    de la session_factory, confirmando (commit) de forma inmediata en lugar de usar
#    la sesión y transacción asociadas a la petición HTTP principal.
#
# 2. POR QUÉ NO PUEDE COMPARTIR LA TRANSACCIÓN:
#    Porque si el intento de autenticación falla (credenciales erróneas o usuario inactivo),
#    la transacción de la petición HTTP se revierte (rollback). Si el intento fallido compartiera
#    esa misma transacción, la reversión borraría el registro del fallo, impidiendo que el sistema
#    cuente los 5 fallos en 60 segundos necesarios para activar el rate limiting (RN-07).
#
# 3. CUÁL ES SU COSTO:
#    Deja filas grabadas de manera permanente en la tabla intento_acceso aun cuando la
#    petición termine en error HTTP (401 o 429), consumiendo espacio de almacenamiento.
# ==============================================================================
async def registrar_intento_independiente(
    session_factory: async_sessionmaker[AsyncSession],
    email: str,
    ip: str,
    exito: bool,
) -> None:
    async with session_factory() as session:
        try:
            intento = IntentoAcceso(
                email=email,
                ip=ip,
                exito=exito,
                cuando=datetime.now(timezone.utc),
            )
            session.add(intento)
            await session.commit()
        except Exception:
            await session.rollback()
            raise


class EventoSeguridadRepository(BaseRepository[EventoSeguridad]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=EventoSeguridad)

    async def registrar(self, actor: str, accion: str) -> EventoSeguridad:
        """Registra un evento de auditoría en la transacción activa (RN-16)."""
        evento = EventoSeguridad(
            actor=actor,
            accion=accion,
            cuando=datetime.now(timezone.utc),
        )
        return await self.add(evento)
