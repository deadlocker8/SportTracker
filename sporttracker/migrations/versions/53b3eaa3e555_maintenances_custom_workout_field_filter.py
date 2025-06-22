"""maintenances_custom_workout_field_filter

Revision ID: 53b3eaa3e555
Revises: f10e23ade4d8
Create Date: 2025-06-22 11:53:41.865401

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Inspector

# revision identifiers, used by Alembic.
revision = '53b3eaa3e555'
down_revision = 'f10e23ade4d8'
branch_labels = None
depends_on = None


def upgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    columns = inspector.get_columns('maintenance')
    columnNames = [column['name'] for column in columns]

    if 'custom_workout_field_id' not in columnNames:
        op.add_column(
            'maintenance',
            sa.Column('custom_workout_field_id', sa.Integer(), nullable=True),
        )

        op.create_foreign_key(None, 'maintenance', 'custom_workout_field', ['custom_workout_field_id'], ['id'])

    if 'custom_workout_field_value' not in columnNames:
        op.add_column(
            'maintenance',
            sa.Column('custom_workout_field_value', sa.String(), nullable=True),
        )


def downgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    columnNames = inspector.get_columns('maintenance')

    if 'custom_workout_field_id' in columnNames:
        op.drop_column('maintenance', 'custom_workout_field_id')

    if 'custom_workout_field_value' in columnNames:
        op.drop_column('maintenance', 'custom_workout_field_value')
