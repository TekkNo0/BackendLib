"""Hacer opcional genero_id en tabla libro para el Global

Revision ID: 0004_libro_genero_nullable
Revises: 0003_trigger_solo_agregado
Create Date: 2026-11-13 18:50:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0004_libro_genero_nullable"
down_revision: Union[str, None] = "0003_trigger_solo_agregado"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "libro",
        "genero_id",
        existing_type=sa.Integer(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "libro",
        "genero_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
