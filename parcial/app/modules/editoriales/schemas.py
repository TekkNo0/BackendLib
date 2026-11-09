from pydantic import BaseModel, ConfigDict, Field


class EditorialCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(min_length=1, max_length=150)


class EditorialResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
