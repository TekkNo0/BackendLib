from unittest.mock import MagicMock
import pytest
from app.core.config import Settings
from app.core.security import generate_dummy_hash
from main import app


@pytest.fixture(autouse=True)
def setup_app_state():
    """Configura app.state para los tests unitarios e integración."""
    settings = Settings(
        POSTGRES_USER="testuser",
        POSTGRES_PASSWORD="testpassword",
        POSTGRES_DB="testdb",
        POSTGRES_HOST="localhost",
        POSTGRES_PORT=5432,
        SECRET_KEY="supersecretkeyforunitandintegrationtestingpurposes",
        BCRYPT_ROUNDS=4,  # Rápido para tests
        ACCESS_TOKEN_EXPIRE_MINUTES=30,
        _env_file=None,
    )
    app.state.settings = settings
    app.state.dummy_hash = generate_dummy_hash(rounds=4)
    app.state.session_factory = MagicMock()
    yield
