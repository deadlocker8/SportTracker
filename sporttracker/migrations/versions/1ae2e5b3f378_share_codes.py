"""share_codes

Revision ID: 1ae2e5b3f378
Revises: 59f2cccf7d63
Create Date: 2024-07-22 21:33:16.731050

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Inspector

# revision identifiers, used by Alembic.
revision = '1ae2e5b3f378'
down_revision = '59f2cccf7d63'
branch_labels = None
depends_on = None


def upgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    columns = inspector.get_columns('planned_tour')
    columnNames = [column['name'] for column in columns]

    if 'share_code' not in columnNames:
        op.add_column(
            'planned_tour',
            sa.Column('share_code', sa.String(), nullable=True, default='NONE'),
        )

    columns = inspector.get_columns('track')
    columnNames = [column['name'] for column in columns]

    if 'share_code' not in columnNames:
        op.add_column(
            'track',
            sa.Column('share_code', sa.String(), nullable=True, default='NONE'),
        )


def downgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    columnNames = inspector.get_columns('planned_tour')

    if 'share_code' in columnNames:
        op.drop_column('planned_tour', 'share_code')
