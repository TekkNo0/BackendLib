from pydantic import BaseModel, ConfigDict, Field


class AutorCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(min_length=1, max_length=150)
    nacionalidad: str = Field(min_length=1, max_length=100)


class AutorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    nacionalidad: str
