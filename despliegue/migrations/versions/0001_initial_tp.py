"""Esquema inicial del TP (Capítulos 1 a 4)

Revision ID: 0001_initial_tp
Revises: 
Create Date: 2026-11-07 14:00:00.000000

Comentario de revisión:
Esta migración establece la línea base del TP original de los capítulos 1 a 4:
- Catálogo: editorial, genero, autor, libro (con ISBN UNIQUE común y sin borrado lógico), libro_autor.
- Clientes: cliente (sin usuario_id) y perfil_cliente.
- Ventas: venta y renglon_venta.
Todos los índices de claves foráneas y restricciones CHECK fueron auditados manualmente.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0001_initial_tp'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Tablas de catálogo
    op.create_table(
        'editorial',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nombre', name='uq_editorial_nombre')
    )
    op.create_index(op.f('ix_editorial_nombre'), 'editorial', ['nombre'], unique=True)

    op.create_table(
        'genero',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nombre', name='uq_genero_nombre')
    )
    op.create_index(op.f('ix_genero_nombre'), 'genero', ['nombre'], unique=True)

    op.create_table(
        'autor',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(), nullable=False),
        sa.Column('nacionalidad', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_autor_nombre'), 'autor', ['nombre'], unique=False)

    op.create_table(
        'libro',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('isbn', sa.String(), nullable=False),
        sa.Column('titulo', sa.String(), nullable=False),
        sa.Column('precio', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('stock', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('editorial_id', sa.Integer(), nullable=False),
        sa.Column('genero_id', sa.Integer(), nullable=False),
        sa.CheckConstraint('precio > 0', name='chk_libro_precio_positivo'),
        sa.CheckConstraint('stock >= 0', name='chk_libro_stock_no_negativo'),
        sa.ForeignKeyConstraint(['editorial_id'], ['editorial.id'], name='fk_libro_editorial'),
        sa.ForeignKeyConstraint(['genero_id'], ['genero.id'], name='fk_libro_genero'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('isbn', name='uq_libro_isbn_original')
    )
    op.create_index(op.f('ix_libro_isbn'), 'libro', ['isbn'], unique=False)
    op.create_index(op.f('ix_libro_titulo'), 'libro', ['titulo'], unique=False)
    op.create_index(op.f('ix_libro_editorial_id'), 'libro', ['editorial_id'], unique=False)
    op.create_index(op.f('ix_libro_genero_id'), 'libro', ['genero_id'], unique=False)

    op.create_table(
        'libro_autor',
        sa.Column('libro_id', sa.Integer(), nullable=False),
        sa.Column('autor_id', sa.Integer(), nullable=False),
        sa.Column('rol', sa.String(), nullable=False, server_default='autor'),
        sa.Column('orden', sa.Integer(), nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['autor_id'], ['autor.id'], name='fk_libro_autor_autor', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['libro_id'], ['libro.id'], name='fk_libro_autor_libro', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('libro_id', 'autor_id')
    )
    op.create_index(op.f('ix_libro_autor_libro_id'), 'libro_autor', ['libro_id'], unique=False)
    op.create_index(op.f('ix_libro_autor_autor_id'), 'libro_autor', ['autor_id'], unique=False)

    # 2. Tablas de clientes
    op.create_table(
        'cliente',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uq_cliente_email')
    )
    op.create_index(op.f('ix_cliente_email'), 'cliente', ['email'], unique=True)

    op.create_table(
        'perfil_cliente',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cliente_id', sa.Integer(), nullable=False),
        sa.Column('telefono', sa.String(), nullable=False),
        sa.Column('direccion', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['cliente_id'], ['cliente.id'], name='fk_perfil_cliente_cliente', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cliente_id', name='uq_perfil_cliente_cliente_id')
    )
    op.create_index(op.f('ix_perfil_cliente_cliente_id'), 'perfil_cliente', ['cliente_id'], unique=True)

    # 3. Tablas de ventas
    op.create_table(
        'venta',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cliente_id', sa.Integer(), nullable=False),
        sa.Column('fecha', sa.DateTime(timezone=True), nullable=False),
        sa.Column('total', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.ForeignKeyConstraint(['cliente_id'], ['cliente.id'], name='fk_venta_cliente'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_venta_cliente_id'), 'venta', ['cliente_id'], unique=False)

    op.create_table(
        'renglon_venta',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('venta_id', sa.Integer(), nullable=False),
        sa.Column('libro_id', sa.Integer(), nullable=False),
        sa.Column('cantidad', sa.Integer(), nullable=False),
        sa.Column('precio_unitario', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.CheckConstraint('cantidad > 0', name='chk_renglon_cantidad_positiva'),
        sa.ForeignKeyConstraint(['libro_id'], ['libro.id'], name='fk_renglon_venta_libro'),
        sa.ForeignKeyConstraint(['venta_id'], ['venta.id'], name='fk_renglon_venta_venta', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_renglon_venta_venta_id'), 'renglon_venta', ['venta_id'], unique=False)
    op.create_index(op.f('ix_renglon_venta_libro_id'), 'renglon_venta', ['libro_id'], unique=False)


def downgrade() -> None:
    op.drop_table('renglon_venta')
    op.drop_table('venta')
    op.drop_table('perfil_cliente')
    op.drop_table('cliente')
    op.drop_table('libro_autor')
    op.drop_table('libro')
    op.drop_table('autor')
    op.drop_table('genero')
    op.drop_table('editorial')
