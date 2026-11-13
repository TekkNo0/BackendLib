import re
from pydantic import BaseModel, ConfigDict, Field, field_validator

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ClienteCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=3, max_length=255)

    @field_validator("email")
    @classmethod
    def validar_email(cls, v: str) -> str:
        valor = v.strip().lower()
        if not _EMAIL_RE.match(valor):
            raise ValueError("El formato del email no es válido.")
        return valor


class ClienteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    email: str
