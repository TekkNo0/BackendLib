from pathlib import Path
from unittest.mock import MagicMock, patch
import importlib.util


def test_trigger_migration_file_and_revisions():
    """Valida la estructura y encadenamiento de la migración manual del trigger."""
    migration_path = Path(__file__).resolve().parent.parent / "migrations" / "versions" / "0003_trigger_solo_agregado.py"
    assert migration_path.exists(), "La migración 0003_trigger_solo_agregado.py debe existir"

    spec = importlib.util.spec_from_file_location("migration_0003", migration_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.revision == "0003_trigger_solo_agregado"
    assert module.down_revision == "0002_parcial_modelos"
    assert hasattr(module, "upgrade")
    assert hasattr(module, "downgrade")
    assert "comentario de revisión y lectura previa" in module.__doc__.lower()


def test_trigger_migration_sql_statements():
    """Valida que upgrade y downgrade ejecuten las sentencias SQL esperadas."""
    migration_path = Path(__file__).resolve().parent.parent / "migrations" / "versions" / "0003_trigger_solo_agregado.py"
    spec = importlib.util.spec_from_file_location("migration_0003", migration_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Probar upgrade()
    with patch("alembic.op.execute") as mock_execute:
        module.upgrade()
        assert mock_execute.call_count == 2
        calls = [c.args[0] for c in mock_execute.call_args_list]
        assert any("fn_proteger_movimiento_stock_solo_agregado" in sql for sql in calls)
        assert any("tr_movimiento_stock_solo_agregado" in sql for sql in calls)
        assert any("BEFORE UPDATE OR DELETE ON movimiento_stock" in sql for sql in calls)

    # Probar downgrade()
    with patch("alembic.op.execute") as mock_execute:
        module.downgrade()
        assert mock_execute.call_count == 2
        calls = [c.args[0] for c in mock_execute.call_args_list]
        assert any("DROP TRIGGER IF EXISTS tr_movimiento_stock_solo_agregado" in sql for sql in calls)
        assert any("DROP FUNCTION IF EXISTS fn_proteger_movimiento_stock_solo_agregado" in sql for sql in calls)


def test_solo_agregado_sql_script_for_case_c14():
    """Valida que el archivo test/solo_agregado.sql exista y tenga el flujo completo del Caso C-14."""
    sql_path = Path(__file__).resolve().parent / "solo_agregado.sql"
    assert sql_path.exists(), "test/solo_agregado.sql debe existir para el caso C-14"

    content = sql_path.read_text(encoding="utf-8")
    assert "INSERT INTO movimiento_stock" in content
    assert "UPDATE movimiento_stock" in content
    assert "DELETE FROM movimiento_stock" in content
    assert "SELECT" in content
    assert "movimiento_stock" in content
