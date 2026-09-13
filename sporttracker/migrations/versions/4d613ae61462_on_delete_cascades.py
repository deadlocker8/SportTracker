"""on delete cascades

Revision ID: 4d613ae61462
Revises: 32518ae760bb
Create Date: 2026-09-13

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Inspector

# revision identifiers, used by Alembic.
revision = '4d613ae61462'
down_revision = '32518ae760bb'
branch_labels = None
depends_on = None


def __get_foreign_keys(table_name: str):
    return Inspector.from_engine(op.get_bind().engine).get_foreign_keys(table_name)


def __set_fk_ondelete(table_name: str, column: str, referred_table: str, ondelete: str):
    foreignKeys = __get_foreign_keys(table_name)
    matchingKeys = [
        key for key in foreignKeys if key['referred_table'] == referred_table and column in key['constrained_columns']
    ]

    if any(key.get('options', {}).get('ondelete') == ondelete for key in matchingKeys):
        return

    for key in matchingKeys:
        name = key['name']
        if name is not None:
            op.drop_constraint(name, table_name, type_='foreignkey')

    op.create_foreign_key(None, table_name, referred_table, [column], ['id'], ondelete=ondelete)


def __delete_orphan_rows(table_name: str, referred_table: str, column: str):
    connection = op.get_bind()
    connection.execute(sa.text(f'DELETE FROM {table_name} WHERE {column} NOT IN (SELECT id FROM {referred_table})'))


def upgrade():
    # delete orphan rows before adding foreign keys to tables that previously had none
    __delete_orphan_rows('heart_rate_data', 'workout', 'workout_id')
    __delete_orphan_rows('fitness_workout_category', 'workout', 'workout_id')
    __delete_orphan_rows('gpx_visited_tile', 'workout', 'workout_id')
    __delete_orphan_rows('gpx_planned_tile', 'planned_tour', 'planned_tour_id')

    # ON DELETE CASCADE: user references
    cascadeUserTables = [
        'workout',
        'participant',
        'custom_workout_field',
        'distance_workout_info_item',
        'body_weight',
        'month_goal_count',
        'month_goal_distance',
        'month_goal_duration',
        'maintenance',
        'notification',
        'notification_settings',
        'ntfy_settings',
        'planned_tour',
        'long_distance_tour',
        'filter_state_maintenance',
        'filter_state_planned_tour',
        'filter_state_quick',
        'filter_state_tile_hunting',
    ]
    for tableName in cascadeUserTables:
        __set_fk_ondelete(tableName, 'user_id', 'user', 'CASCADE')

    # ON DELETE CASCADE: workout hierarchies
    __set_fk_ondelete('distance_workout', 'id', 'workout', 'CASCADE')
    __set_fk_ondelete('fitness_workout', 'id', 'workout', 'CASCADE')
    __set_fk_ondelete('heart_rate_data', 'workout_id', 'workout', 'CASCADE')
    __set_fk_ondelete('fitness_workout_category', 'workout_id', 'workout', 'CASCADE')
    __set_fk_ondelete('gpx_visited_tile', 'workout_id', 'workout', 'CASCADE')
    __set_fk_ondelete('gpx_planned_tile', 'planned_tour_id', 'planned_tour', 'CASCADE')
    __set_fk_ondelete('maintenance_event_instance', 'maintenance_id', 'maintenance', 'CASCADE')

    # ON DELETE CASCADE: association tables
    __set_fk_ondelete('workout_participant_association', 'workout_id', 'workout', 'CASCADE')
    __set_fk_ondelete('workout_participant_association', 'participant_id', 'participant', 'CASCADE')
    __set_fk_ondelete('planned_tour_user_association', 'planned_tour_id', 'planned_tour', 'CASCADE')
    __set_fk_ondelete('planned_tour_user_association', 'user_id', 'user', 'CASCADE')
    __set_fk_ondelete('distance_workout_planned_tour_association', 'distance_workout_id', 'distance_workout', 'CASCADE')
    __set_fk_ondelete('distance_workout_planned_tour_association', 'planned_tour_id', 'planned_tour', 'CASCADE')
    __set_fk_ondelete('long_distance_tour_user_association', 'long_distance_tour_id', 'long_distance_tour', 'CASCADE')
    __set_fk_ondelete('long_distance_tour_user_association', 'user_id', 'user', 'CASCADE')
    __set_fk_ondelete(
        'long_distance_tour_planned_tour_association', 'long_distance_tour_id', 'long_distance_tour', 'CASCADE'
    )
    __set_fk_ondelete('long_distance_tour_planned_tour_association', 'planned_tour_id', 'planned_tour', 'CASCADE')

    # ON DELETE SET NULL: optional references
    __set_fk_ondelete('distance_workout', 'gpx_metadata_id', 'gpx_metadata', 'SET NULL')
    __set_fk_ondelete('planned_tour', 'gpx_metadata_id', 'gpx_metadata', 'SET NULL')
    __set_fk_ondelete('maintenance', 'custom_workout_field_id', 'custom_workout_field', 'SET NULL')
    __set_fk_ondelete('filter_state_maintenance', 'custom_workout_field_id', 'custom_workout_field', 'SET NULL')


def __drop_fk(table_name: str, column: str, referred_table: str):
    foreignKeys = __get_foreign_keys(table_name)
    matchingKeys = [
        key for key in foreignKeys if key['referred_table'] == referred_table and column in key['constrained_columns']
    ]

    for key in matchingKeys:
        name = key['name']
        if name is not None:
            op.drop_constraint(name, table_name, type_='foreignkey')


def __restore_default_fk(table_name: str, column: str, referred_table: str):
    __drop_fk(table_name, column, referred_table)
    op.create_foreign_key(None, table_name, referred_table, [column], ['id'])


def downgrade():
    cascadeUserTables = [
        'workout',
        'participant',
        'custom_workout_field',
        'distance_workout_info_item',
        'body_weight',
        'month_goal_count',
        'month_goal_distance',
        'month_goal_duration',
        'maintenance',
        'notification',
        'notification_settings',
        'ntfy_settings',
        'planned_tour',
        'long_distance_tour',
        'filter_state_maintenance',
        'filter_state_planned_tour',
        'filter_state_quick',
        'filter_state_tile_hunting',
    ]
    for tableName in cascadeUserTables:
        __restore_default_fk(tableName, 'user_id', 'user')

    __restore_default_fk('distance_workout', 'id', 'workout')
    __restore_default_fk('fitness_workout', 'id', 'workout')
    __restore_default_fk('heart_rate_data', 'workout_id', 'workout')
    __restore_default_fk('fitness_workout_category', 'workout_id', 'workout')
    __restore_default_fk('gpx_visited_tile', 'workout_id', 'workout')
    __restore_default_fk('gpx_planned_tile', 'planned_tour_id', 'planned_tour')
    __restore_default_fk('maintenance_event_instance', 'maintenance_id', 'maintenance')

    __restore_default_fk('workout_participant_association', 'workout_id', 'workout')
    __restore_default_fk('workout_participant_association', 'participant_id', 'participant')
    __restore_default_fk('planned_tour_user_association', 'planned_tour_id', 'planned_tour')
    __restore_default_fk('planned_tour_user_association', 'user_id', 'user')
    __restore_default_fk('distance_workout_planned_tour_association', 'distance_workout_id', 'distance_workout')
    __restore_default_fk('distance_workout_planned_tour_association', 'planned_tour_id', 'planned_tour')
    __restore_default_fk('long_distance_tour_user_association', 'long_distance_tour_id', 'long_distance_tour')
    __restore_default_fk('long_distance_tour_user_association', 'user_id', 'user')
    __restore_default_fk('long_distance_tour_planned_tour_association', 'long_distance_tour_id', 'long_distance_tour')
    __restore_default_fk('long_distance_tour_planned_tour_association', 'planned_tour_id', 'planned_tour')

    __restore_default_fk('distance_workout', 'gpx_metadata_id', 'gpx_metadata')
    __restore_default_fk('planned_tour', 'gpx_metadata_id', 'gpx_metadata')
    __restore_default_fk('maintenance', 'custom_workout_field_id', 'custom_workout_field')
    __restore_default_fk('filter_state_maintenance', 'custom_workout_field_id', 'custom_workout_field')
