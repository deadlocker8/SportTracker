"""persisted_filter_states

Revision ID: e6d14acbc655
Revises: 53b3eaa3e555
Create Date: 2025-06-29 14:14:50.756354

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Inspector, text

# revision identifiers, used by Alembic.
revision = 'e6d14acbc655'
down_revision = '53b3eaa3e555'
branch_labels = None
depends_on = None


def upgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    tableNames = inspector.get_table_names()

    if 'filter_state_maintenance' not in tableNames:
        op.create_table(
            'filter_state_maintenance',
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('custom_workout_field_id', sa.Integer(), nullable=True),
            sa.Column('custom_workout_field_value', sa.String(), nullable=True),
            sa.ForeignKeyConstraint(
                ['user_id'],
                ['user.id'],
            ),
            sa.ForeignKeyConstraint(
                ['custom_workout_field_id'],
                ['custom_workout_field.id'],
            ),
            sa.PrimaryKeyConstraint('user_id'),
        )

    connection = op.get_bind()
    existingRows = connection.execute(text('SELECT * FROM filter_state_maintenance;')).fetchall()
    if not existingRows:
        userIdRows = connection.execute(text('SELECT "user".id FROM "user";')).fetchall()
        for userIdRow in userIdRows:
            connection.execute(
                text(
                    f"INSERT INTO filter_state_maintenance (user_id, custom_workout_field_id, custom_workout_field_value) VALUES ('{userIdRow[0]}', NULL, NULL);"
                )
            )


def downgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    tableNames = inspector.get_table_names()

    if 'filter_state_maintenance' in tableNames:
        op.drop_table('filter_state_maintenance')
