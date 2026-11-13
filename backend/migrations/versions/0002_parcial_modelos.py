"""Evolución del esquema para Parcial (Capítulos 5 y 6)

Revision ID: 0002_parcial_modelos
Revises: 0001_initial_tp
Create Date: 2026-11-07 14:05:00.000000

Comentario de revisión y lectura previa:
Esta migración incorpora las extensiones de seguridad, control de stock y borrado lógico requeridas por el Parcial:
1. Seguridad:
   - Tabla usuario (con email unique, hash bcrypt y banderas).
   - Tabla asignacion_rol (con check constraint de roles y el índice único parcial uq_asignacion_rol_abierta WHERE revocada_en IS NULL).
   - Tabla intento_acceso (con índice compuesto email, ip, cuando).
   - Tabla evento_seguridad (actor en texto para registrar 'SISTEMA' o emails).
2. Clientes:
   - Se añade la columna usuario_id (FK a usuario.id, nullable, UNIQUE) para permitir acceso opcional por la web.
3. Catálogo y Borrado Lógico:
   - Se añade la columna borrado_en (timestamptz) a la tabla libro.
   - Se remueve la restricción de UNIQUE común sobre isbn y se reemplaza por el índice único parcial uq_libro_isbn_vigente WHERE borrado_en IS NULL (RN-01, RN-13).
4. Inventario:
   - Se crea la tabla movimiento_stock (con CHECK cantidad <> 0 e índices en todas las claves foráneas).
Nota de revisión: Se corrigió manualmente la creación de índices con cláusula WHERE ('postgresql_where') para garantizar compatibilidad con PostgreSQL.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0002_parcial_modelos'
down_revision: Union[str, None] = '0001_initial_tp'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Tablas de Seguridad
    op.create_table(
        'usuario',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('nombre', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('debe_cambiar_password', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uq_usuario_email')
    )
    op.create_index(op.f('ix_usuario_email'), 'usuario', ['email'], unique=True)

    op.create_table(
        'asignacion_rol',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('rol', sa.String(), nullable=False),
        sa.Column('desde', sa.DateTime(timezone=True), nullable=False),
        sa.Column('vence_en', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revocada_en', sa.DateTime(timezone=True), nullable=True),
        sa.Column('otorgada_por', sa.Integer(), nullable=True),
        sa.CheckConstraint("rol IN ('ADMIN', 'VENDEDOR', 'CLIENTE')", name='chk_rol_valido'),
        sa.ForeignKeyConstraint(['otorgada_por'], ['usuario.id'], name='fk_asignacion_rol_otorgada_por'),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuario.id'], name='fk_asignacion_rol_usuario', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_asignacion_rol_usuario_id'), 'asignacion_rol', ['usuario_id'], unique=False)
    op.create_index(op.f('ix_asignacion_rol_otorgada_por'), 'asignacion_rol', ['otorgada_por'], unique=False)
    
    # Índice único parcial: un usuario tiene a lo sumo una asignación abierta por rol (RN-03)
    op.create_index(
        'uq_asignacion_rol_abierta',
        'asignacion_rol',
        ['usuario_id', 'rol'],
        unique=True,
        postgresql_where=sa.text('revocada_en IS NULL')
    )

    op.create_table(
        'intento_acceso',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cuando', sa.DateTime(timezone=True), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('ip', sa.String(), nullable=False),
        sa.Column('exito', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_intento_acceso_email'), 'intento_acceso', ['email'], unique=False)
    op.create_index('ix_intento_acceso_email_ip_cuando', 'intento_acceso', ['email', 'ip', 'cuando'], unique=False)

    op.create_table(
        'evento_seguridad',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cuando', sa.DateTime(timezone=True), nullable=False),
        sa.Column('actor', sa.String(), nullable=False),
        sa.Column('accion', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. Modificación a cliente: agregar usuario_id (1 a 1 opcional)
    op.add_column('cliente', sa.Column('usuario_id', sa.Integer(), nullable=True))
    op.create_unique_constraint('uq_cliente_usuario_id', 'cliente', ['usuario_id'])
    op.create_foreign_key('fk_cliente_usuario', 'cliente', 'usuario', ['usuario_id'], ['id'])
    op.create_index(op.f('ix_cliente_usuario_id'), 'cliente', ['usuario_id'], unique=True)

    # 3. Modificación a libro: borrado lógico e índice único parcial en ISBN
    op.add_column('libro', sa.Column('borrado_en', sa.DateTime(timezone=True), nullable=True))
    op.drop_constraint('uq_libro_isbn_original', 'libro', type_='unique')
    op.create_index(
        'uq_libro_isbn_vigente',
        'libro',
        ['isbn'],
        unique=True,
        postgresql_where=sa.text('borrado_en IS NULL')
    )

    # 4. Tabla de Movimientos de Stock
    op.create_table(
        'movimiento_stock',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('libro_id', sa.Integer(), nullable=False),
        sa.Column('venta_id', sa.Integer(), nullable=True),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('cantidad', sa.Integer(), nullable=False),
        sa.Column('motivo', sa.String(), nullable=False),
        sa.Column('cuando', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('cantidad <> 0', name='chk_movimiento_cantidad_no_cero'),
        sa.ForeignKeyConstraint(['libro_id'], ['libro.id'], name='fk_movimiento_stock_libro'),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuario.id'], name='fk_movimiento_stock_usuario'),
        sa.ForeignKeyConstraint(['venta_id'], ['venta.id'], name='fk_movimiento_stock_venta', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_movimiento_stock_libro_id'), 'movimiento_stock', ['libro_id'], unique=False)
    op.create_index(op.f('ix_movimiento_stock_venta_id'), 'movimiento_stock', ['venta_id'], unique=False)
    op.create_index(op.f('ix_movimiento_stock_usuario_id'), 'movimiento_stock', ['usuario_id'], unique=False)


def downgrade() -> None:
    # 4. Dropear movimiento_stock
    op.drop_index(op.f('ix_movimiento_stock_usuario_id'), table_name='movimiento_stock')
    op.drop_index(op.f('ix_movimiento_stock_venta_id'), table_name='movimiento_stock')
    op.drop_index(op.f('ix_movimiento_stock_libro_id'), table_name='movimiento_stock')
    op.drop_table('movimiento_stock')

    # 3. Revertir libro
    op.drop_index('uq_libro_isbn_vigente', table_name='libro', postgresql_where=sa.text('borrado_en IS NULL'))
    op.create_unique_constraint('uq_libro_isbn_original', 'libro', ['isbn'])
    op.drop_column('libro', 'borrado_en')

    # 2. Revertir cliente
    op.drop_index(op.f('ix_cliente_usuario_id'), table_name='cliente')
    op.drop_constraint('fk_cliente_usuario', 'cliente', type_='foreignkey')
    op.drop_constraint('uq_cliente_usuario_id', 'cliente', type_='unique')
    op.drop_column('cliente', 'usuario_id')

    # 1. Dropear tablas de seguridad
    op.drop_table('evento_seguridad')
    op.drop_index('ix_intento_acceso_email_ip_cuando', table_name='intento_acceso')
    op.drop_index(op.f('ix_intento_acceso_email'), table_name='intento_acceso')
    op.drop_table('intento_acceso')
    op.drop_index('uq_asignacion_rol_abierta', table_name='asignacion_rol', postgresql_where=sa.text('revocada_en IS NULL'))
    op.drop_index(op.f('ix_asignacion_rol_otorgada_por'), table_name='asignacion_rol')
    op.drop_index(op.f('ix_asignacion_rol_usuario_id'), table_name='asignacion_rol')
    op.drop_table('asignacion_rol')
    op.drop_index(op.f('ix_usuario_email'), table_name='usuario')
    op.drop_table('usuario')
