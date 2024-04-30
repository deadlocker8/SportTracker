"""user_planned_tour_last_viewed_date

Revision ID: c71a496c3bc2
Revises: 772f84a6f268
Create Date: 2024-04-30 18:48:32.266967

"""
from datetime import datetime

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Inspector

# revision identifiers, used by Alembic.
revision = 'c71a496c3bc2'
down_revision = '772f84a6f268'
branch_labels = None
depends_on = None


def upgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    columns = inspector.get_columns('user')
    columnNames = [column['name'] for column in columns]

    if 'planned_tours_last_viewed_date' not in columnNames:
        op.add_column(
            'user',
            sa.Column('planned_tours_last_viewed_date', sa.DateTime(), nullable=True),
        )

    op.execute(
        f'UPDATE "user" SET planned_tours_last_viewed_date=\'{datetime.now().isoformat()}\' WHERE planned_tours_last_viewed_date IS NULL;')


def downgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    columnNames = inspector.get_columns('user')

    if 'planned_tours_last_viewed_date' in columnNames:
        op.drop_column('user', 'planned_tours_last_viewed_date')
