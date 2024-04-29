"""planned_tours_direction

Revision ID: 7cac13f41c7e
Revises: 59f2cccf7d63
Create Date: 2024-04-30 00:12:45.247352

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Inspector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '7cac13f41c7e'
down_revision = '59f2cccf7d63'
branch_labels = None
depends_on = None


def upgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    columns = inspector.get_columns('planned_tour')
    columnNames = [column['name'] for column in columns]

    if 'direction' not in columnNames:
        op.add_column(
            'planned_tour',
            sa.Column(
                'direction',
                postgresql.ENUM(name='traveldirection', create_type=False),
                nullable=True,
                default='SINGLE',
            ),
        )

    op.execute("UPDATE planned_tour SET direction='SINGLE' WHERE direction IS NULL;")


def downgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    columnNames = inspector.get_columns('planned_tour')

    if 'direction' in columnNames:
        op.drop_column('planned_tour', 'direction')
