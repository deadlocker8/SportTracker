"""workout_categories

Revision ID: f5965fa22d86
Revises: 698959745124
Create Date: 2025-01-14 22:41:44.503565

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Inspector

# revision identifiers, used by Alembic.
revision = 'f5965fa22d86'
down_revision = '698959745124'
branch_labels = None
depends_on = None


def upgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    tableNames = inspector.get_table_names()

    if 'workout_category' not in tableNames:
        op.create_table(
            'workout_category',
            sa.Column('track_id', sa.Integer(), nullable=False),
            sa.Column(
                'workout_category_type',
                sa.Enum('ARMS', 'LEGS', 'CORE', 'YOGA', name='workoutcategorytype'),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint('track_id', 'workout_category_type'),
        )


def downgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    tableNames = inspector.get_table_names()

    if 'workout_category' in tableNames:
        op.drop_table('workout_category')
