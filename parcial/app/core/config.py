from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Variables de base de datos
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str  # Obligatorio: sin valor por defecto
    POSTGRES_DB: str = "libreria"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    # Parámetros del pool de SQLAlchemy
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    SQL_ECHO: bool = False

    # Seguridad y JWT
    SECRET_KEY: str  # Obligatorio: clave de firma sin valor por defecto
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    COOKIE_SECURE: bool = False
    BCRYPT_ROUNDS: int = 12

    # Límite de intentos de login
    LOGIN_RATE_LIMIT_ATTEMPTS: int = 5
    LOGIN_RATE_LIMIT_WINDOW_SECONDS: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @computed_field
    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
