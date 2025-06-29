"""persisted_filter_states

Revision ID: e6d14acbc655
Revises: 53b3eaa3e555
Create Date: 2025-06-29 14:14:50.756354

"""

import json

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Inspector, text
from sqlalchemy.dialects import postgresql

from sporttracker.logic.model.PlannedTour import TravelDirection
from sporttracker.logic.model.TravelType import TravelType

# revision identifiers, used by Alembic.
revision = 'e6d14acbc655'
down_revision = '53b3eaa3e555'
branch_labels = None
depends_on = None


def upgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    tableNames = inspector.get_table_names()

    __handle_new_table_maintenance_filter_state(tableNames)

    __handle_new_table_planned_tour_filter_state(tableNames)


def downgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    tableNames = inspector.get_table_names()

    if 'filter_state_maintenance' in tableNames:
        op.drop_table('filter_state_maintenance')

    if 'filter_state_planned_tour' in tableNames:
        op.drop_table('filter_state_planned_tour')


def __handle_new_table_maintenance_filter_state(tableNames):
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


def __handle_new_table_planned_tour_filter_state(tableNames):
    if 'filter_state_planned_tour' not in tableNames:
        op.create_table(
            'filter_state_planned_tour',
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('is_done_selected', sa.Boolean(), nullable=False),
            sa.Column('is_todo_selected', sa.Boolean(), nullable=False),
            sa.Column('arrival_methods', postgresql.JSON(astext_type=sa.Text()), nullable=True),
            sa.Column('departure_methods', postgresql.JSON(astext_type=sa.Text()), nullable=True),
            sa.Column('directions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
            sa.Column('name_filter', sa.Boolean(), nullable=True),
            sa.Column('minimum_distance', sa.Integer(), nullable=True),
            sa.Column('maximum_distance', sa.Integer(), nullable=True),
            sa.Column('is_long_distance_tours_include_selected', sa.Boolean(), nullable=False),
            sa.Column('is_long_distance_tours_exclude_selected', sa.Boolean(), nullable=False),
            sa.ForeignKeyConstraint(
                ['user_id'],
                ['user.id'],
            ),
            sa.PrimaryKeyConstraint('user_id'),
        )
    connection = op.get_bind()
    existingRows = connection.execute(text('SELECT * FROM filter_state_planned_tour;')).fetchall()
    if not existingRows:
        userIdRows = connection.execute(text('SELECT "user".id FROM "user";')).fetchall()

        arrivalMethods = json.dumps({travelType.name: True for travelType in TravelType})
        departureMethods = json.dumps({travelType.name: True for travelType in TravelType})
        directions = json.dumps({travelDirection.name: True for travelDirection in TravelDirection})

        for userIdRow in userIdRows:
            connection.execute(
                text(
                    f'INSERT INTO filter_state_planned_tour (user_id, '
                    f'is_done_selected, '
                    f'is_todo_selected, '
                    f'arrival_methods, '
                    f'departure_methods, '
                    f'directions, '
                    f'name_filter, '
                    f'minimum_distance, '
                    f'maximum_distance, '
                    f'is_long_distance_tours_include_selected, '
                    f'is_long_distance_tours_exclude_selected'
                    f" ) VALUES ('{userIdRow[0]}', "
                    f'True, '
                    f'True, '
                    f"'{arrivalMethods}', "
                    f"'{departureMethods}', "
                    f"'{directions}', "
                    f'NULL, '
                    f'NULL, '
                    f'NULL, '
                    f'True, '
                    f'True);'
                )
            )
