"""tile_hunting_max_cluster

Revision ID: c3f1a9d4b7e2
Revises: d54abb934a4f
Create Date: 2026-10-10 12:30:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Inspector

# revision identifiers, used by Alembic.
revision = '3865d076b199'
down_revision = 'd54abb934a4f'
branch_labels = None
depends_on = None


def __get_column_names(table_name: str) -> list[str]:
    inspector = Inspector.from_engine(op.get_bind().engine)
    return [column['name'] for column in inspector.get_columns(table_name)]


def upgrade():
    columnNames = __get_column_names('filter_state_tile_hunting')

    if 'is_own_tours_active' not in columnNames:
        op.add_column('filter_state_tile_hunting', sa.Column('is_show_max_cluster_active', sa.Boolean(), nullable=True))

    op.execute(
        'UPDATE filter_state_tile_hunting SET is_show_max_cluster_active=False WHERE is_show_max_cluster_active IS NULL;'
    )
    op.alter_column(
        'filter_state_tile_hunting', 'is_show_max_cluster_active', existing_type=sa.Boolean(), nullable=False
    )


def downgrade():
    columnNames = __get_column_names('filter_state_planned_tour')

    if 'is_show_max_cluster_active' in columnNames:
        op.drop_column('filter_state_tile_hunting', 'is_show_max_cluster_active')
