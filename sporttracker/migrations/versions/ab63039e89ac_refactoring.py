"""refactoring

Revision ID: ab63039e89ac
Revises: f5965fa22d86
Create Date: 2025-01-28 21:11:19.365756

"""

import logging

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Inspector, text
from sqlalchemy.dialects import postgresql

from sporttracker import Constants

# revision identifiers, used by Alembic.
revision = 'ab63039e89ac'
down_revision = 'dff4668aee2d'
branch_labels = None
depends_on = None

LOGGER = logging.getLogger(Constants.APP_NAME)


def upgrade():
    __handle_workout_category()

    __handle_gpx_visited_tiles()

    __handle_custom_track_field()

    __handle_track_info_item()

    __update_type_column('maintenance')

    __update_type_column('month_goal_count')

    __update_type_column('month_goal_distance')

    __update_type_column('month_goal_duration')

    __update_type_column('planned_tour')

    __handle_tracks()

    __handle_workout_participant_association()

    __handle_distance_workout_planned_tour_association()

    inspector = Inspector.from_engine(op.get_bind().engine)
    tableNames = inspector.get_table_names()
    if 'track' in tableNames:
        op.drop_table('track')


def __handle_workout_category():
    inspector = Inspector.from_engine(op.get_bind().engine)
    tableNames = inspector.get_table_names()

    if 'fitness_workout_category' not in tableNames:
        LOGGER.debug('Create table "fitness_workout_category"')
        op.create_table(
            'fitness_workout_category',
            sa.Column('workout_id', sa.Integer(), nullable=False),
            sa.Column(
                'fitness_workout_category_type',
                sa.Enum('ARMS', 'LEGS', 'CORE', 'YOGA', name='fitnessworkoutcategorytype'),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint('workout_id', 'fitness_workout_category_type'),
        )


def __handle_gpx_visited_tiles():
    inspector = Inspector.from_engine(op.get_bind().engine)
    columns = inspector.get_columns('gpx_visited_tile')
    columnNames = [column['name'] for column in columns]

    if 'workout_id' not in columnNames:
        connection = op.get_bind()
        rows = connection.execute(text('SELECT * FROM gpx_visited_tile;')).fetchall()

        op.drop_table('gpx_visited_tile')

        LOGGER.debug('Create table "gpx_visited_tile"')
        op.create_table(
            'gpx_visited_tile',
            sa.Column('workout_id', sa.Integer(), nullable=False),
            sa.Column('x', sa.Integer(), nullable=False),
            sa.Column('y', sa.Integer(), nullable=False),
            sa.PrimaryKeyConstraint('workout_id', 'x', 'y'),
        )

        for row in rows:
            LOGGER.debug(f'  Migrate gpx_visited_tile: {row}')
            workoutId, x, y = row
            connection.execute(
                text(f"INSERT INTO gpx_visited_tile (workout_id, x, y) VALUES ('{workoutId}', '{x}', '{y}');")
            )


def __handle_custom_track_field():
    inspector = Inspector.from_engine(op.get_bind().engine)
    tableNames = inspector.get_table_names()

    if 'custom_workout_field' not in tableNames:
        LOGGER.debug('Create table "custom_track_field"')
        op.create_table(
            'custom_workout_field',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column(
                'type',
                sa.Enum('STRING', 'INTEGER', 'FLOAT', name='customworkoutfieldtype'),
                nullable=True,
            ),
            sa.Column(
                'workout_type',
                postgresql.ENUM(name='workouttype', create_type=False),
                nullable=True,
            ),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('is_required', sa.Boolean(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(
                ['user_id'],
                ['user.id'],
            ),
            sa.PrimaryKeyConstraint('id'),
        )

    if 'custom_track_field' in tableNames:
        LOGGER.debug('  Migrate data from "custom_track_field" to "custom_workout_field')
        connection = op.get_bind()
        rows = connection.execute(text('SELECT * FROM custom_track_field ORDER BY id;')).fetchall()

        highestId = 0
        for row in rows:
            LOGGER.debug(f'  Migrate custom_track_field: {row}')
            entryId, fieldType, trackType, name, isRequired, userId = row
            trackType = __track_type_to_workout_type(trackType)

            connection.execute(
                text(
                    f"INSERT INTO custom_workout_field (id, type, workout_type, name, is_required, user_id) VALUES ('{entryId}', '{fieldType}', '{trackType}', '{name}', '{isRequired}', '{userId}');"
                )
            )
            highestId = entryId

        op.drop_table('custom_track_field')

        __restart_sequence(connection, 'custom_workout_field_id_seq', highestId)


def __handle_track_info_item():
    inspector = Inspector.from_engine(op.get_bind().engine)
    tableNames = inspector.get_table_names()

    if 'distance_workout_info_item' not in tableNames:
        LOGGER.debug('Create table "distance_workout_info_item"')
        op.create_table(
            'distance_workout_info_item',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column(
                'type',
                sa.Enum(
                    'DISTANCE',
                    'DURATION',
                    'SPEED',
                    'AVERAGE_HEART_RATE',
                    'ELEVATION_SUM',
                    name='distanceworkoutinfoitemtype',
                ),
                nullable=True,
            ),
            sa.Column('is_activated', sa.Boolean(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(
                ['user_id'],
                ['user.id'],
            ),
            sa.PrimaryKeyConstraint('id'),
        )

    if 'track_info_item' in tableNames:
        LOGGER.debug('  Migrate data from "track_info_item" to "distance_workout_info_item')
        connection = op.get_bind()
        rows = connection.execute(text('SELECT * FROM track_info_item ORDER BY id;')).fetchall()

        highestId = 0
        for row in rows:
            LOGGER.debug(f'  Migrate track_info_item: {row}')
            entryId, trackType, isActivated, userId = row
            trackType = __track_type_to_workout_type(trackType)
            connection.execute(
                text(
                    f"INSERT INTO distance_workout_info_item (id, type, is_activated, user_id) VALUES ('{entryId}', '{trackType}', '{isActivated}', '{userId}');"
                )
            )
            highestId = entryId

        op.drop_table('track_info_item')

        __restart_sequence(connection, 'distance_workout_info_item_id_seq', highestId)


def __update_type_column(tableName: str):
    inspector = Inspector.from_engine(op.get_bind().engine)
    columns = inspector.get_columns(tableName)

    column = [c for c in columns if c['name'] == 'type'][0]

    if column['type'].name == 'tracktype':  # type: ignore[attr-defined]
        connection = op.get_bind()
        rows = connection.execute(text(f'SELECT id, type FROM {tableName};')).fetchall()

        LOGGER.debug(f'Update column "type" in "{tableName}"')
        op.alter_column(tableName, 'type', new_column_name='type_old')

        op.add_column(
            tableName,
            sa.Column('type', postgresql.ENUM(name='workouttype', create_type=False), nullable=True),
        )

        for row in rows:
            LOGGER.debug(f'  Migrate {tableName} row: {row}')
            entryId, trackType = row
            trackType = __track_type_to_workout_type(trackType)

            connection.execute(text(f"UPDATE {tableName} SET type='{trackType}' WHERE id={entryId};"))

        op.drop_column(tableName, 'type_old')


def __track_type_to_workout_type(trackType: str) -> str:
    if trackType == 'WORKOUT':
        return 'FITNESS'

    return trackType


def __handle_workout_participant_association():
    inspector = Inspector.from_engine(op.get_bind().engine)
    tableNames = inspector.get_table_names()

    if 'workout_participant_association' not in tableNames:
        LOGGER.debug('Create table "workout_participant_association"')
        op.create_table(
            'workout_participant_association',
            sa.Column('workout_id', sa.Integer(), nullable=True),
            sa.Column('participant_id', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(
                ['participant_id'],
                ['participant.id'],
            ),
            sa.ForeignKeyConstraint(
                ['workout_id'],
                ['workout.id'],
            ),
        )

    if 'track_participant_association' in tableNames:
        LOGGER.debug('  Migrate data from "track_participant_association " to "workout_participant_association')
        connection = op.get_bind()
        rows = connection.execute(text('SELECT * FROM track_participant_association;')).fetchall()

        for row in rows:
            LOGGER.debug(f'  Migrate track_participant_association: {row}')
            trackId, participantId = row

            connection.execute(
                text(
                    f"INSERT INTO workout_participant_association (workout_id, participant_id) VALUES ('{trackId}', '{participantId}');"
                )
            )

        op.drop_table('track_participant_association')


def __handle_distance_workout_planned_tour_association():
    inspector = Inspector.from_engine(op.get_bind().engine)
    tableNames = inspector.get_table_names()

    if 'distance_workout_planned_tour_association' not in tableNames:
        LOGGER.debug('Create table "distance_workout_planned_tour_association"')
        op.create_table(
            'distance_workout_planned_tour_association',
            sa.Column('distance_workout_id', sa.Integer(), nullable=True),
            sa.Column('planned_tour_id', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(
                ['distance_workout_id'],
                ['distance_workout.id'],
            ),
            sa.ForeignKeyConstraint(
                ['planned_tour_id'],
                ['planned_tour.id'],
            ),
        )

    if 'track_planned_tour_association' in tableNames:
        LOGGER.debug(
            '  Migrate data from "track_planned_tour_association" to "distance_workout_planned_tour_association'
        )
        connection = op.get_bind()
        rows = connection.execute(text('SELECT * FROM track_planned_tour_association;')).fetchall()

        for row in rows:
            LOGGER.debug(f'  Migrate track_planned_tour_association: {row}')
            trackId, plannedTourId = row

            connection.execute(
                text(
                    f"INSERT INTO distance_workout_planned_tour_association (distance_workout_id, planned_tour_id) VALUES ('{trackId}', '{plannedTourId}');"
                )
            )

        op.drop_table('track_planned_tour_association')


def __handle_tracks():
    inspector = Inspector.from_engine(op.get_bind().engine)
    tableNames = inspector.get_table_names()

    if 'distance_workout_planned_tour_association' not in tableNames:
        LOGGER.debug('Create table "workout"')
        op.create_table(
            'workout',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column(
                'workout_type',
                postgresql.ENUM(name='workouttype', create_type=False),
                nullable=True,
            ),
            sa.Column('class_type', sa.String(), nullable=True),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('start_time', sa.DateTime(), nullable=False),
            sa.Column('duration', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('average_heart_rate', sa.Integer(), nullable=True),
            sa.Column('custom_fields', postgresql.JSON(astext_type=sa.Text()), nullable=True),
            sa.ForeignKeyConstraint(
                ['user_id'],
                ['user.id'],
            ),
            sa.PrimaryKeyConstraint('id'),
        )

        LOGGER.debug('Create table "distance_workout"')
        op.create_table(
            'distance_workout',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('distance', sa.Integer(), nullable=False),
            sa.Column('elevation_sum', sa.Integer(), nullable=True),
            sa.Column('share_code', sa.String(), nullable=True),
            sa.Column('gpx_metadata_id', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(
                ['gpx_metadata_id'],
                ['gpx_metadata.id'],
            ),
            sa.ForeignKeyConstraint(
                ['id'],
                ['workout.id'],
            ),
            sa.PrimaryKeyConstraint('id'),
        )

        LOGGER.debug('Create table "fitness_workout"')
        op.create_table(
            'fitness_workout',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column(
                'fitness_workout_type',
                postgresql.ENUM(name='fitnessworkouttype', create_type=False),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(
                ['id'],
                ['workout.id'],
            ),
            sa.PrimaryKeyConstraint('id'),
        )

    if 'track' in tableNames:
        LOGGER.debug('  Migrate data from "track"')
        connection = op.get_bind()
        rows = connection.execute(
            text(
                'SELECT track."id", track."type", track."name", track."startTime", track."duration", track."distance", track."averageHeartRate", track."elevationSum", track."user_id", track."share_code", track."gpx_metadata_id", track."custom_fields" FROM track ORDER BY track."id";'
            )
        ).fetchall()

        highestId = 0
        for row in rows:
            LOGGER.debug(f'  Migrate track: {row}')
            (
                entryId,
                trackType,
                name,
                startTime,
                duration,
                distance,
                averageHeartRate,
                elevationSum,
                userId,
                shareCode,
                gpxMetadataId,
                custom_fields,
            ) = row
            trackType = __track_type_to_workout_type(trackType)
            classType = __get_class_type(trackType)
            custom_fields = custom_fields.__repr__().replace("'", '"')
            averageHeartRate = 'NULL' if averageHeartRate is None else f"'{averageHeartRate}'"
            elevationSum = 'NULL' if elevationSum is None else f"'{elevationSum}'"
            shareCode = 'NULL' if shareCode is None else f"'{shareCode}'"
            gpxMetadataId = 'NULL' if gpxMetadataId is None else f"'{gpxMetadataId}'"
            duration = 0 if duration is None else duration

            connection.execute(
                text(
                    f"INSERT INTO workout (id, type, class_type, name, start_time, duration, user_id, average_heart_rate, custom_fields) VALUES ('{entryId}', '{trackType}', '{classType}', '{name}', '{startTime}', '{duration}', '{userId}', {averageHeartRate}, '{custom_fields}');"
                )
            )
            highestId = entryId

            if trackType == 'FITNESS':
                connection.execute(
                    text(
                        f"INSERT INTO fitness_workout (id, fitness_workout_type) VALUES ('{entryId}', 'DURATION_BASED');"
                    )
                )
            else:
                connection.execute(
                    text(
                        f"INSERT INTO distance_workout (id, distance, elevation_sum, share_code, gpx_metadata_id) VALUES ('{entryId}', '{distance}', {elevationSum}, {shareCode}, {gpxMetadataId});"
                    )
                )

        __restart_sequence(connection, 'workout_id_seq', highestId)


def __get_class_type(workoutType: str) -> str:
    if workoutType == 'FITNESS':
        return 'fitness_workout'

    return 'distance_workout'


def __restart_sequence(connection, sequenceName, lastId):
    LOGGER.debug(f'  Set {sequenceName} to {lastId + 1}')
    connection.execute(text(f'ALTER SEQUENCE {sequenceName} RESTART WITH {lastId + 1};'))


def downgrade():
    pass
