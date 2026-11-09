import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any
import bcrypt
import jwt

# Semáforo para limitar la cantidad de llamadas concurrentes a bcrypt y proteger el event loop
BCRYPT_SEMAPHORE = asyncio.Semaphore(10)


def generate_dummy_hash(rounds: int = 12) -> str:
    """Genera un hash ficticio de bcrypt una sola vez en el lifespan para mitigar timing attacks."""
    salt = bcrypt.gensalt(rounds=rounds)
    return bcrypt.hashpw(b"dummy_timing_protection_hash_UTN_prog3", salt).decode("utf-8")


def _hash_password_sync(password: str, rounds: int) -> str:
    salt = bcrypt.gensalt(rounds=rounds)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def _verify_password_sync(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


async def hash_password(password: str, rounds: int = 12) -> str:
    """Calcula el hash de contraseña fuera del bucle de eventos mediante to_thread y bajo semáforo."""
    async with BCRYPT_SEMAPHORE:
        return await asyncio.to_thread(_hash_password_sync, password, rounds)


async def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica la contraseña fuera del bucle de eventos bajo semáforo."""
    async with BCRYPT_SEMAPHORE:
        return await asyncio.to_thread(_verify_password_sync, plain_password, hashed_password)


def create_access_token(
    data: dict[str, Any],
    secret_key: str,
    algorithm: str = "HS256",
    expires_delta: timedelta | None = None,
) -> str:
    """Emite un token JWT con sub, exp y claims pasados en data."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, secret_key, algorithm=algorithm)


def decode_access_token(token: str, secret_key: str, algorithms: list[str]) -> dict[str, Any]:
    """Decodifica y valida un token JWT firmado."""
    return jwt.decode(token, secret_key, algorithms=algorithms)
