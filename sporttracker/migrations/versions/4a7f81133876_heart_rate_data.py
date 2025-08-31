"""heart_rate_data

Revision ID: 4a7f81133876
Revises: 60cb8e6fa4bc
Create Date: 2025-08-31 15:21:37.853589

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Inspector

# revision identifiers, used by Alembic.
revision = '4a7f81133876'
down_revision = '60cb8e6fa4bc'
branch_labels = None
depends_on = None


def upgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    tableNames = inspector.get_table_names()

    if 'heart_rate_data' not in tableNames:
        op.create_table(
            'heart_rate_data',
            sa.Column('workout_id', sa.Integer(), nullable=False, index=True),
            sa.Column('timestamp', sa.DateTime(), nullable=False),
            sa.Column('bpm', sa.Integer(), nullable=False),
            sa.PrimaryKeyConstraint('workout_id', 'timestamp', 'bpm'),
        )


def downgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    tableNames = inspector.get_table_names()

    if 'heart_rate_data' in tableNames:
        op.drop_table('heart_rate_data')
