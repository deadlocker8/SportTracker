"""filter_tours_by_share_status

Revision ID: d54abb934a4f
Revises: 4d613ae61462
Create Date: 2026-09-27 21:15:37.939864

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Inspector

# revision identifiers, used by Alembic.
revision = 'd54abb934a4f'
down_revision = '4d613ae61462'
branch_labels = None
depends_on = None


def __get_column_names(table_name: str) -> list[str]:
    inspector = Inspector.from_engine(op.get_bind().engine)
    return [column['name'] for column in inspector.get_columns(table_name)]


def upgrade():
    columnNames = __get_column_names('filter_state_planned_tour')

    if 'is_own_tours_active' not in columnNames:
        op.add_column('filter_state_planned_tour', sa.Column('is_own_tours_active', sa.Boolean(), nullable=True))

    op.execute('UPDATE filter_state_planned_tour SET is_own_tours_active=True WHERE is_own_tours_active IS NULL;')
    op.alter_column('filter_state_planned_tour', 'is_own_tours_active', existing_type=sa.Boolean(), nullable=False)

    if 'is_shared_with_others_active' not in columnNames:
        op.add_column(
            'filter_state_planned_tour', sa.Column('is_shared_with_others_active', sa.Boolean(), nullable=True)
        )

    op.execute(
        'UPDATE filter_state_planned_tour SET is_shared_with_others_active=True WHERE is_shared_with_others_active IS NULL;'
    )
    op.alter_column(
        'filter_state_planned_tour', 'is_shared_with_others_active', existing_type=sa.Boolean(), nullable=False
    )

    if 'is_shared_by_others_active' not in columnNames:
        op.add_column('filter_state_planned_tour', sa.Column('is_shared_by_others_active', sa.Boolean(), nullable=True))

    op.execute(
        'UPDATE filter_state_planned_tour SET is_shared_by_others_active=True WHERE is_shared_by_others_active IS NULL;'
    )
    op.alter_column(
        'filter_state_planned_tour', 'is_shared_by_others_active', existing_type=sa.Boolean(), nullable=False
    )


def downgrade():
    columnNames = __get_column_names('filter_state_planned_tour')

    if 'is_own_tours_active' in columnNames:
        op.drop_column('filter_state_planned_tour', 'is_own_tours_active')

    if 'is_shared_with_others_active' in columnNames:
        op.drop_column('filter_state_planned_tour', 'is_shared_with_others_active')

    if 'is_shared_by_others_active' in columnNames:
        op.drop_column('filter_state_planned_tour', 'is_shared_by_others_active')
