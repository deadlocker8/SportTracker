"""workout_types

Revision ID: 698959745124
Revises: dff4668aee2d
Create Date: 2025-01-14 20:53:48.424452

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Inspector

# revision identifiers, used by Alembic.
revision = '698959745124'
down_revision = 'dff4668aee2d'
branch_labels = None
depends_on = None


def upgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    columns = inspector.get_columns('track')
    columnNames = [column['name'] for column in columns]

    if 'workout_type' not in columnNames:
        op.add_column(
            'track',
            sa.Column(
                'workout_type',
                sa.Enum('DURATION_BASED', 'REPETITION_BASED', name='workouttype'),
                nullable=True,
            ),
        )

        op.execute(
            "UPDATE track SET workout_type='DURATION_BASED' WHERE type = 'WORKOUT' AND workout_type IS NULL;"
        )


def downgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    columnNames = inspector.get_columns('track')

    if 'workout_type' in columnNames:
        op.drop_column('track', 'workout_type')
