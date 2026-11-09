from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.security import create_access_token, hash_password, verify_password
from app.modules.clientes.models import Cliente
from app.modules.usuarios.models import AsignacionRol, Usuario
from app.modules.usuarios.repository import registrar_intento_independiente
from app.modules.usuarios.schemas import (
    AuthYoResponse,
    CambiarPasswordRequest,
    LoginRequest,
    LoginResponse,
    RegistroClienteRequest,
    UsuarioResponse,
)
from app.modules.usuarios.unit_of_work import UsuariosUnitOfWork


class AuthService:
    """Servicio de reglas de negocio de autenticación y usuarios.
    
    Regla: Recibe el Unit of Work y lo abre con `async with uow:` para las operaciones transaccionales.
    Nunca construye el Unit of Work directamente.
    """

    async def registrar_cliente(
        self,
        uow: UsuariosUnitOfWork,
        req: RegistroClienteRequest,
        rounds: int = 12,
    ) -> Usuario:
        """Auto-registro atómico de cliente (RN-02).
        
        Crea el usuario, su rol CLIENTE y su ficha de cliente en un solo Unit of Work:
        o quedan las tres filas, o ninguna. Si ya existe un cliente o usuario con ese correo,
        da 409 y no se apropia de la ficha.
        """
        # Calcular hash de contraseña fuera del bucle y antes de abrir la transacción
        pw_hash = await hash_password(req.password, rounds=rounds)

        async with uow:
            # Validar unicidad previa en cliente y usuario para dar 409 legible
            if await uow.clientes.get_by_email(req.email):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Ya existe un cliente registrado con ese correo electrónico",
                )
            if await uow.usuarios.get_by_email(req.email):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Ya existe un usuario registrado con ese correo electrónico",
                )

            # 1. Crear Usuario
            usuario = Usuario(
                email=req.email,
                nombre=req.nombre,
                password_hash=pw_hash,
                activo=True,
                debe_cambiar_password=False,
            )
            await uow.usuarios.add(usuario)

            # 2. Asignar Rol CLIENTE
            asignacion = AsignacionRol(
                usuario_id=usuario.id,  # type: ignore
                rol="CLIENTE",
                desde=datetime.now(timezone.utc),
            )
            await uow.roles.add(asignacion)

            # 3. Crear Ficha de Cliente
            cliente = Cliente(
                nombre=req.nombre,
                email=req.email,
                usuario_id=usuario.id,
            )
            await uow.clientes.add(cliente)

            # 4. Registrar auditoría (RN-16)
            await uow.eventos.registrar(
                actor=usuario.email,
                accion="Auto-registro de cliente con rol CLIENTE",
            )

        return usuario

    async def login(
        self,
        uow: UsuariosUnitOfWork,
        session_factory: async_sessionmaker[AsyncSession],
        req: LoginRequest,
        ip: str,
        dummy_hash: str,
        secret_key: str,
        algorithm: str = "HS256",
        expire_minutes: int = 30,
    ) -> tuple[str, LoginResponse]:
        """Flujo de login con rate limiting en base (RN-07) y mitigación de timing attack (RN-08)."""
        # PASO 1: Límite de intentos (RN-07)
        fallos = await uow.intentos.contar_fallos_recientes(
            email=req.email,
            ip=ip,
            ventana_segundos=60,
        )
        if fallos >= 5:
            # Responde 429 con cabecera Retry-After sin calcular ningún hash
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Demasiados intentos fallidos. Intente nuevamente en 60 segundos.",
                headers={"Retry-After": "60"},
            )

        # PASO 2: Obtener usuario
        usuario = await uow.usuarios.get_by_email(req.email)

        # PASO 3: Verificación contra hash de usuario o hash ficticio (RN-08)
        if usuario is None or not usuario.activo:
            await verify_password(req.password, dummy_hash)
            await registrar_intento_independiente(
                session_factory=session_factory,
                email=req.email,
                ip=ip,
                exito=False,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas",
            )

        password_correcta = await verify_password(req.password, usuario.password_hash)
        if not password_correcta:
            await registrar_intento_independiente(
                session_factory=session_factory,
                email=req.email,
                ip=ip,
                exito=False,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas",
            )

        # Login correcto: anota éxito en intento_acceso (reinicia la cuenta de fallos posteriores)
        await registrar_intento_independiente(
            session_factory=session_factory,
            email=req.email,
            ip=ip,
            exito=True,
        )

        # Consultar roles vigentes en base en el momento de emisión
        roles_vigentes = await uow.roles.get_roles_vigentes(usuario.id)  # type: ignore

        # Generar token JWT firmado
        token = create_access_token(
            data={
                "sub": str(usuario.id),
                "email": usuario.email,
                "roles": roles_vigentes,
            },
            secret_key=secret_key,
            algorithm=algorithm,
            expires_delta=timedelta(minutes=expire_minutes),
        )

        response_body = LoginResponse(
            mensaje="Sesión iniciada",
            debe_cambiar_password=usuario.debe_cambiar_password,
            expira_en_segundos=expire_minutes * 60,
        )
        return token, response_body

    async def cambiar_password(
        self,
        uow: UsuariosUnitOfWork,
        usuario_id: int,
        req: CambiarPasswordRequest,
        rounds: int = 12,
    ) -> dict[str, str]:
        """Actualiza la contraseña del usuario, limpia bandera y audita en evento_seguridad (RN-16)."""
        usuario = await uow.usuarios.get_by_id(usuario_id)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado",
            )

        # Validar contraseña actual
        if not await verify_password(req.password_actual, usuario.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Contraseña actual incorrecta",
            )

        # Hashear nueva contraseña fuera de la transacción
        nuevo_hash = await hash_password(req.password_nueva, rounds=rounds)

        async with uow:
            usuario.password_hash = nuevo_hash
            usuario.debe_cambiar_password = False
            await uow.usuarios.update(usuario)

            # Auditar en la misma transacción (RN-16)
            await uow.eventos.registrar(
                actor=usuario.email,
                accion="Cambio de contraseña",
            )

        return {"mensaje": "Contraseña actualizada exitosamente"}

    async def get_yo(
        self,
        uow: UsuariosUnitOfWork,
        usuario_id: int,
        token_roles: list[str],
    ) -> AuthYoResponse:
        """Devuelve el usuario actual, sus roles vigentes en base y los que dice el token."""
        usuario = await uow.usuarios.get_by_id(usuario_id)
        if not usuario or not usuario.activo:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no autenticado o inactivo",
            )

        roles_vigentes = await uow.roles.get_roles_vigentes(usuario.id)  # type: ignore

        return AuthYoResponse(
            usuario=UsuarioResponse(
                id=usuario.id,  # type: ignore
                email=usuario.email,
                nombre=usuario.nombre,
                activo=usuario.activo,
                debe_cambiar_password=usuario.debe_cambiar_password,
            ),
            roles_vigentes=roles_vigentes,
            roles_token=token_roles,
        )

    async def alta_personal(
        self,
        uow: UsuariosUnitOfWork,
        admin_email: str,
        nombre: str,
        email: str,
        password_provisoria: str,
        rounds: int = 12,
    ) -> Usuario:
        """Alta de personal por parte de un ADMIN con contraseña provisoria y auditoría (RN-16)."""
        pw_hash = await hash_password(password_provisoria, rounds=rounds)

        async with uow:
            if await uow.usuarios.get_by_email(email):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Ya existe un usuario registrado con ese correo electrónico",
                )

            usuario = Usuario(
                email=email,
                nombre=nombre,
                password_hash=pw_hash,
                activo=True,
                debe_cambiar_password=True,
            )
            await uow.usuarios.add(usuario)

            await uow.eventos.registrar(
                actor=admin_email,
                accion=f"Alta de personal para {email}",
            )

        return usuario

    async def listar_roles(
        self,
        uow: UsuariosUnitOfWork,
        usuario_id: int,
    ) -> list[AsignacionRol]:
        """Lista el historial de roles de un usuario."""
        usuario = await uow.usuarios.get_by_id(usuario_id)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado",
            )
        return await uow.roles.get_roles_por_usuario(usuario_id)

    async def asignar_rol(
        self,
        uow: UsuariosUnitOfWork,
        admin_id: int,
        admin_email: str,
        usuario_id: int,
        rol: str,
        vence_en_iso: str | None,
    ) -> AsignacionRol:
        """Asigna un rol a un usuario, cerrando la fila previa si estaba vencida (RN-03, RN-16)."""
        usuario = await uow.usuarios.get_by_id(usuario_id)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado",
            )

        vence_en_dt = datetime.fromisoformat(vence_en_iso) if vence_en_iso else None
        now = datetime.now(timezone.utc)

        async with uow:
            abierta = await uow.roles.get_asignacion_abierta(usuario_id, rol)
            if abierta:
                # Si está abierta y no vencida -> 409
                if abierta.vence_en is None or abierta.vence_en > now:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"El usuario ya posee una asignación abierta para el rol {rol}",
                    )
                # Si estaba vencida, reasignar cierra la fila anterior y abre una nueva
                abierta.revocada_en = now
                await uow.roles.update(abierta)

            nueva_asig = AsignacionRol(
                usuario_id=usuario_id,
                rol=rol,
                desde=now,
                vence_en=vence_en_dt,
                otorgada_por=admin_id,
            )
            await uow.roles.add(nueva_asig)

            await uow.eventos.registrar(
                actor=admin_email,
                accion=f"Asignación de rol {rol} a usuario {usuario.email}",
            )

        return nueva_asig

    async def revocar_rol(
        self,
        uow: UsuariosUnitOfWork,
        admin_id: int,
        admin_email: str,
        usuario_id: int,
        rol: str,
    ) -> None:
        """Revoca un rol con autoprotección (RN-05) y auditoría en evento_seguridad (RN-16)."""
        usuario = await uow.usuarios.get_by_id(usuario_id)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado",
            )

        rol_upper = rol.upper()

        # RN-05: Autoprotección de administradores
        if rol_upper == "ADMIN":
            if admin_id == usuario_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Un administrador no puede revocarse su propio rol ADMIN",
                )
            admins_vigentes = await uow.roles.contar_admins_vigentes()
            if admins_vigentes <= 1:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="El sistema nunca queda sin administradores vigentes",
                )

        async with uow:
            asignacion = await uow.roles.get_asignacion_abierta(usuario_id, rol_upper)
            if not asignacion:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No se encontró una asignación abierta para el rol {rol_upper}",
                )

            asignacion.revocada_en = datetime.now(timezone.utc)
            await uow.roles.update(asignacion)

            await uow.eventos.registrar(
                actor=admin_email,
                accion=f"Revocación de rol {rol_upper} a usuario {usuario.email}",
            )
