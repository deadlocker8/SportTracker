"""quick_filter_date_range

Revision ID: 32518ae760bb
Revises: a6c5e61e0f1a
Create Date: 2026-08-03 21:47:40.753492

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Inspector

# revision identifiers, used by Alembic.
revision = '32518ae760bb'
down_revision = 'a6c5e61e0f1a'
branch_labels = None
depends_on = None


def __get_column_names(table_name: str) -> list[str]:
    inspector = Inspector.from_engine(op.get_bind().engine)
    return [column['name'] for column in inspector.get_columns(table_name)]


def upgrade():
    columnNames = __get_column_names('filter_state_quick')
    if 'date_from' not in columnNames:
        op.add_column('filter_state_quick', sa.Column('date_from', sa.Date(), nullable=True))

    if 'date_to' not in columnNames:
        op.add_column('filter_state_quick', sa.Column('date_to', sa.Date(), nullable=True))


def downgrade():
    columnNames = __get_column_names('filter_state_quick')
    if 'date_to' in columnNames:
        op.drop_column('filter_state_quick', 'date_to')

    if 'date_from' in columnNames:
        op.drop_column('filter_state_quick', 'date_from')
