from pathlib import Path
import pytest


def test_all_16_canonical_http_test_cases_present():
    """Valida que existan los 16 archivos .http de prueba para los casos C-01 a C-16."""
    test_dir = Path(__file__).resolve().parent
    expected_files = [
        "caso_c01_parametro_invalido.http",
        "caso_c02_registro_conflictos.http",
        "caso_c03_cookie_login.http",
        "caso_c04_timing_login.http",
        "caso_c05_rate_limit.http",
        "caso_c06_permisos_y_lo_propio.http",
        "caso_c07_revocar_rol_en_vivo.http",
        "caso_c08_autoproteccion_admin.http",
        "caso_c09_cambio_obligatorio.http",
        "caso_c10_venta_valida.http",
        "caso_c11_venta_insuficiente.http",
        "caso_c12_venta_inexistente.http",
        "caso_c13_reponer_baja_reuso_isbn.http",
        "caso_c14_solo_agregado.sql",
        "caso_c15_eager_loading_n1.http",
        "caso_c16_filtros_seguridad_paginacion.http",
    ]

    for filename in expected_files:
        filepath = test_dir / filename
        assert filepath.exists(), f"El archivo {filename} debe existir en test/"
        content = filepath.read_text(encoding="utf-8")
        assert len(content) > 50, f"El archivo {filename} no debe estar vacío"


def test_parcial_evidencia_artifacts_present():
    """Valida la presencia y contenido de los archivos de evidencia en parcial/evidencia/."""
    evidencia_dir = Path(__file__).resolve().parent.parent / "evidencia"
    assert evidencia_dir.exists(), "La carpeta parcial/evidencia debe existir"

    c14_file = evidencia_dir / "c14_psql_output.txt"
    assert c14_file.exists(), "c14_psql_output.txt debe existir"
    c14_content = c14_file.read_text(encoding="utf-8")
    assert "movimiento_stock es de sólo agregado" in c14_content or "no se permite UPDATE" in c14_content
    assert "no se permite DELETE" in c14_content

    c15_file = evidencia_dir / "c15_consultas_n1_output.txt"
    assert c15_file.exists(), "c15_consultas_n1_output.txt debe existir"
    c15_content = c15_file.read_text(encoding="utf-8")
    assert "selectinload" in c15_content.lower()
    assert "GET /ventas/1" in c15_content
    assert "GET /ventas/2" in c15_content


def test_readme_meets_spec_and_instructions():
    """Valida que parcial/README.md contenga las secciones obligatorias requeridas por consigna."""
    readme_path = Path(__file__).resolve().parent.parent / "README.md"
    assert readme_path.exists(), "parcial/README.md debe existir"

    content = readme_path.read_text(encoding="utf-8")
    assert "Integrantes" in content
    assert "alembic upgrade head" in content
    assert "python seed.py" in content
    assert "SECRET_KEY" in content
    assert "requirements.txt" in content
    assert "uvicorn" in content


def test_final_zip_deliverable_structure_and_exclusions():
    """Valida que el archivo comprimido Parcial_Cap1a6_Grupo.zip cumpla con todas las reglas de entrega."""
    import zipfile

    zip_path = Path(__file__).resolve().parent.parent.parent / "Parcial_Cap1a6_Grupo.zip"
    assert zip_path.exists(), "El archivo ZIP de entrega Parcial_Cap1a6_Grupo.zip debe existir"

    with zipfile.ZipFile(zip_path, "r") as z:
        names = z.namelist()
        assert any(n.startswith("parcial/") for n in names)
        assert any(n.startswith("despliegue/") for n in names)
        assert not any(n.startswith("openspec/") for n in names)
        assert not any(n.startswith(".git/") for n in names)
        assert not any("__pycache__" in n for n in names)
        assert not any(".venv" in n for n in names)
        assert not any(".pytest_cache" in n for n in names)
        assert not any(n.endswith((".pyc", ".pyo", ".pyd")) for n in names)
        assert not any(n.split("/")[-1] == ".env" for n in names)

