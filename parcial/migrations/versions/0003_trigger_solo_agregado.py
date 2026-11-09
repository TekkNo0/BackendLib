"""Trigger de sólo agregado sobre movimiento_stock (RN-12)

Revision ID: 0003_trigger_solo_agregado
Revises: 0002_parcial_modelos
Create Date: 2026-11-07 14:15:00.000000

Comentario de revisión y lectura previa (Ejercicio 2 y 7):
Esta migración fue escrita a mano porque la comparación automática de Alembic (--autogenerate)
no detecta funciones PL/pgSQL ni disparadores (triggers) de base de datos.
Instala la regla de negocio RN-12: movimiento_stock es estrictamente de sólo agregado.
Cualquier intento de UPDATE o DELETE sobre movimiento_stock es rechazado con una excepción
fatal a nivel de base de datos, impidiendo modificaciones manuales o por código accidental.
"""
from typing import Sequence, Union
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '0003_trigger_solo_agregado'
down_revision: Union[str, None] = '0002_parcial_modelos'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
    CREATE OR REPLACE FUNCTION fn_proteger_movimiento_stock_solo_agregado()
    RETURNS TRIGGER AS $$
    BEGIN
        IF TG_OP = 'UPDATE' THEN
            RAISE EXCEPTION 'movimiento_stock es de sólo agregado: no se permite UPDATE en la fila %', OLD.id;
        ELSIF TG_OP = 'DELETE' THEN
            RAISE EXCEPTION 'movimiento_stock es de sólo agregado: no se permite DELETE en la fila %', OLD.id;
        END IF;
        RETURN NULL;
    END;
    $$ LANGUAGE plpgsql;
    """)

    op.execute("""
    CREATE TRIGGER tr_movimiento_stock_solo_agregado
    BEFORE UPDATE OR DELETE ON movimiento_stock
    FOR EACH ROW
    EXECUTE FUNCTION fn_proteger_movimiento_stock_solo_agregado();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS tr_movimiento_stock_solo_agregado ON movimiento_stock;")
    op.execute("DROP FUNCTION IF EXISTS fn_proteger_movimiento_stock_solo_agregado();")
