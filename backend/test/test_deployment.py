from pathlib import Path


def test_dockerfile_configuration_meets_requirements():
    """Valida la configuración del Dockerfile para el despliegue en VPS (Ejercicio 9)."""
    dockerfile_path = Path(__file__).resolve().parent.parent.parent / "despliegue" / "Dockerfile"
    assert dockerfile_path.exists(), "El archivo Dockerfile debe existir en despliegue/"

    content = dockerfile_path.read_text(encoding="utf-8")

    # 1. Imagen base python:3.12-alpine (< 100 MB)
    assert "FROM python:3.12-alpine" in content

    # 2. Usuario sin privilegios no-root
    assert "adduser" in content and "appuser" in content
    assert "USER appuser" in content

    # 3. Instalación de requirements antes de copiar el código
    idx_req = content.find("COPY requirements.txt")
    idx_code = content.find("COPY . .")
    assert idx_req != -1 and idx_code != -1
    assert idx_req < idx_code, "requirements.txt debe copiarse e instalarse antes de copiar el código fuente"
    assert "--no-cache-dir" in content

    # 4. HEALTHCHECK apuntando a 127.0.0.1 (no localhost)
    assert "HEALTHCHECK" in content
    assert "127.0.0.1:8000/health/ready" in content
    assert "http://localhost" not in content

    # 5. Migraciones automáticas al arranque
    assert "alembic upgrade head" in content
    assert "0.0.0.0" in content


def test_dockerignore_excludes_secrets_and_caches():
    """Valida que .dockerignore excluya archivos sensibles y cachés."""
    dockerignore_path = Path(__file__).resolve().parent.parent.parent / "despliegue" / ".dockerignore"
    assert dockerignore_path.exists(), "El archivo .dockerignore debe existir en despliegue/"

    lines = [line.strip() for line in dockerignore_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    assert ".env" in lines
    assert ".venv" in lines
    assert ".git" in lines
    assert "__pycache__" in lines


def test_env_example_has_no_plaintext_passwords():
    """Valida que env.example proporcione plantilla limpia sin secretos reales."""
    env_example_path = Path(__file__).resolve().parent.parent.parent / "despliegue" / "env.example"
    assert env_example_path.exists(), "El archivo env.example debe existir en despliegue/"

    content = env_example_path.read_text(encoding="utf-8")
    assert "DATABASE_URL=" in content
    assert "postgresql+asyncpg://" in content
    assert "secret" not in content.lower() or "password" not in content.lower()


def test_deploy_doc_and_evidences_present():
    """Valida la presencia de DEPLOY.md y los 8 archivos de evidencia D-01 a D-08."""
    despliegue_dir = Path(__file__).resolve().parent.parent.parent / "despliegue"

    deploy_md = despliegue_dir / "DEPLOY.md"
    assert deploy_md.exists(), "DEPLOY.md debe existir en despliegue/"
    deploy_content = deploy_md.read_text(encoding="utf-8")
    assert "host.docker.internal:host-gateway" in deploy_content
    assert "unless-stopped" in deploy_content

    evidencia_dir = despliegue_dir / "evidencia"
    assert evidencia_dir.exists(), "La carpeta despliegue/evidencia/ debe existir"

    for i in range(1, 9):
        ev_file = evidencia_dir / f"d{i:02d}_"
        matching = list(evidencia_dir.glob(f"d{i:02d}_*.txt"))
        assert len(matching) == 1, f"Falta archivo de evidencia para caso D-{i:02d}"
        assert matching[0].stat().st_size > 0, f"El archivo de evidencia {matching[0].name} está vacío"
