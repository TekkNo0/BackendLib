from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def validate_password_72_bytes(value: str) -> str:
    """Valida que la contraseña no supere los 72 bytes en UTF-8 para evitar errores 500 de bcrypt v5."""
    if len(value.encode("utf-8")) > 72:
        raise ValueError("La contraseña no puede superar los 72 bytes.")
    if len(value) < 4:
        raise ValueError("La contraseña debe tener al menos 4 caracteres.")
    return value


class RegistroClienteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def check_password_bytes(cls, v: str) -> str:
        return validate_password_72_bytes(v)


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def check_password_bytes(cls, v: str) -> str:
        return validate_password_72_bytes(v)


class LoginResponse(BaseModel):
    mensaje: str = "Sesión iniciada"
    debe_cambiar_password: bool
    expira_en_segundos: int = 1800


class CambiarPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    password_actual: str
    password_nueva: str

    @field_validator("password_actual", "password_nueva")
    @classmethod
    def check_password_bytes(cls, v: str) -> str:
        return validate_password_72_bytes(v)


class UsuarioResponse(BaseModel):
    id: int
    email: str
    nombre: str
    activo: bool
    debe_cambiar_password: bool


class AuthYoResponse(BaseModel):
    usuario: UsuarioResponse
    roles_vigentes: list[str]
    roles_token: list[str]


class AltaPersonalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password_provisoria: str

    @field_validator("password_provisoria")
    @classmethod
    def check_password_bytes(cls, v: str) -> str:
        return validate_password_72_bytes(v)


class AsignarRolRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rol: str = Field(..., description="ADMIN, VENDEDOR o CLIENTE")
    vence_en: str | None = Field(default=None, description="Fecha de expiración con zona horaria en el futuro")

    @field_validator("rol")
    @classmethod
    def check_rol_valido(cls, v: str) -> str:
        v_upper = v.upper()
        if v_upper not in ("ADMIN", "VENDEDOR", "CLIENTE"):
            raise ValueError("El rol debe ser ADMIN, VENDEDOR o CLIENTE.")
        return v_upper

    @field_validator("vence_en")
    @classmethod
    def check_fecha_futura_con_timezone(cls, v: str | None) -> str | None:
        if v is None:
            return None
        from datetime import datetime, timezone
        try:
            dt = datetime.fromisoformat(v)
        except Exception as exc:
            raise ValueError("Formato de fecha inválido. Utilice formato ISO 8601.") from exc

        if dt.tzinfo is None:
            raise ValueError("La fecha de vencimiento debe incluir zona horaria.")
        if dt <= datetime.now(timezone.utc):
            raise ValueError("La fecha de vencimiento debe estar en el futuro.")
        return v


class AsignacionRolResponse(BaseModel):
    id: int
    usuario_id: int
    rol: str
    desde: str
    vence_en: str | None
    revocada_en: str | None
    otorgada_por: int | None


class EventoSeguridadResponse(BaseModel):
    id: int
    cuando: str
    actor: str
    accion: str
