from decimal import Decimal
from sqlalchemy import CheckConstraint, Index
from sqlmodel import SQLModel
from app.core.metadata import target_metadata
from app.modules.usuarios.models import Usuario, AsignacionRol, IntentoAcceso, EventoSeguridad
from app.modules.editoriales.models import Editorial
from app.modules.generos.models import Genero
from app.modules.autores.models import Autor
from app.modules.libros.models import Libro, LibroAutor
from app.modules.clientes.models import Cliente, PerfilCliente
from app.modules.ventas.models import Venta, RenglonVenta, MovimientoStock


def test_metadata_contains_all_required_tables():
    """Valida que todas las tablas del modelo de dominio estén presentes en la metadata."""
    expected_tables = {
        "editorial",
        "genero",
        "autor",
        "libro",
        "libro_autor",
        "cliente",
        "perfil_cliente",
        "usuario",
        "asignacion_rol",
        "intento_acceso",
        "evento_seguridad",
        "venta",
        "renglon_venta",
        "movimiento_stock",
    }
    registered_tables = set(target_metadata.tables.keys())
    missing = expected_tables - registered_tables
    assert not missing, f"Faltan tablas en metadata: {missing}"


def test_cliente_usuario_relationship_is_scalar():
    """Valida que Cliente.usuario sea una relación escalar 1-a-1 y no una lista."""
    mapper = SQLModel._sa_registry.mappers
    cliente_mapper = None
    for m in mapper:
        if m.class_ == Cliente:
            cliente_mapper = m
            break
    assert cliente_mapper is not None
    usuario_rel = cliente_mapper.relationships.get("usuario")
    assert usuario_rel is not None
    assert usuario_rel.uselist is False, "Cliente.usuario debe devolver un objeto y no una lista"


def test_partial_unique_indexes_defined():
    """Valida la presencia de índices únicos parciales con postgresql_where."""
    # 1. AsignacionRol: uq_asignacion_rol_abierta WHERE revocada_en IS NULL
    asignacion_table = target_metadata.tables["asignacion_rol"]
    asignacion_indices = {idx.name: idx for idx in asignacion_table.indexes}
    assert "uq_asignacion_rol_abierta" in asignacion_indices
    idx_rol = asignacion_indices["uq_asignacion_rol_abierta"]
    assert idx_rol.unique is True
    assert "revocada_en IS NULL" in str(idx_rol.dialect_options["postgresql"]["where"])

    # 2. Libro: uq_libro_isbn_vigente WHERE borrado_en IS NULL
    libro_table = target_metadata.tables["libro"]
    libro_indices = {idx.name: idx for idx in libro_table.indexes}
    assert "uq_libro_isbn_vigente" in libro_indices
    idx_isbn = libro_indices["uq_libro_isbn_vigente"]
    assert idx_isbn.unique is True
    assert "borrado_en IS NULL" in str(idx_isbn.dialect_options["postgresql"]["where"])


def test_check_constraints_present():
    """Valida que los CHECK constraints obligatorios estén declarados."""
    # Libro: precio > 0 y stock >= 0
    libro_table = target_metadata.tables["libro"]
    libro_checks = {c.name: str(c.sqltext) for c in libro_table.constraints if isinstance(c, CheckConstraint)}
    assert any("precio > 0" in text for text in libro_checks.values())
    assert any("stock >= 0" in text for text in libro_checks.values())

    # RenglonVenta: cantidad > 0
    renglon_table = target_metadata.tables["renglon_venta"]
    renglon_checks = {c.name: str(c.sqltext) for c in renglon_table.constraints if isinstance(c, CheckConstraint)}
    assert any("cantidad > 0" in text for text in renglon_checks.values())

    # MovimientoStock: cantidad <> 0
    mov_table = target_metadata.tables["movimiento_stock"]
    mov_checks = {c.name: str(c.sqltext) for c in mov_table.constraints if isinstance(c, CheckConstraint)}
    assert any("cantidad <> 0" in text for text in mov_checks.values())

    # AsignacionRol: rol IN ('ADMIN', 'VENDEDOR', 'CLIENTE')
    rol_table = target_metadata.tables["asignacion_rol"]
    rol_checks = {c.name: str(c.sqltext) for c in rol_table.constraints if isinstance(c, CheckConstraint)}
    assert any("ADMIN" in text and "VENDEDOR" in text and "CLIENTE" in text for text in rol_checks.values())


def test_composite_index_on_intento_acceso():
    """Valida el índice compuesto en intento_acceso (email, ip, cuando)."""
    table = target_metadata.tables["intento_acceso"]
    indices = {idx.name: [col.name for col in idx.columns] for idx in table.indexes}
    assert "ix_intento_acceso_email_ip_cuando" in indices
    assert indices["ix_intento_acceso_email_ip_cuando"] == ["email", "ip", "cuando"]
