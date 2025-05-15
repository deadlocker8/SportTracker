"""long_distance_tours

Revision ID: 42608807ae69
Revises: ad3012342146
Create Date: 2025-05-15 21:47:45.393975

"""

from datetime import datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Inspector

# revision identifiers, used by Alembic.
revision = '42608807ae69'
down_revision = 'ad3012342146'
branch_labels = None
depends_on = None


def upgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    columns = inspector.get_columns('user')
    columnNames = [column['name'] for column in columns]

    if 'long_distance_tours_last_viewed_date' not in columnNames:
        op.add_column(
            'user',
            sa.Column('long_distance_tours_last_viewed_date', sa.DateTime(), nullable=True),
        )
        op.execute(
            f'UPDATE "user" SET "long_distance_tours_last_viewed_date" = \'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\' WHERE "user"."long_distance_tours_last_viewed_date" IS NULL;'
        )


def downgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    columnNames = inspector.get_columns('user')

    if 'long_distance_tours_last_viewed_date' in columnNames:
        op.drop_column('user', 'long_distance_tours_last_viewed_date')
