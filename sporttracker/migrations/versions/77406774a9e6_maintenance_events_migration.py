"""maintenance_events_migration

Revision ID: 77406774a9e6
Revises: 3c3147e8e24c
Create Date: 2024-12-14 18:55:28.549884

"""

import logging

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text, Inspector
from sqlalchemy.dialects import postgresql

from sporttracker.logic import Constants

revision = '77406774a9e6'
down_revision = '3c3147e8e24c'
branch_labels = None
depends_on = None


LOGGER = logging.getLogger(Constants.APP_NAME)


def __get_table_names() -> list[str]:
    inspector = Inspector.from_engine(op.get_bind().engine)
    return inspector.get_table_names()


def __get_maintenance(connection, typeName: str, description: str, userId: int):
    return connection.execute(
        text(
            f"SELECT maintenance.id FROM maintenance WHERE maintenance.description='{description}' "
            f"AND maintenance.type='{typeName}' AND maintenance.user_id={userId};"
        )
    ).first()


def upgrade():
    tableNames = __get_table_names()

    if 'maintenance_event' in tableNames:
        LOGGER.debug('Migrating existing maintenance events to new database structure')

        if 'maintenance' not in tableNames:
            op.create_table(
                'maintenance',
                sa.Column('id', sa.Integer(), nullable=False),
                sa.Column('type', postgresql.ENUM(name='tracktype', create_type=False), nullable=True),
                sa.Column('description', sa.String(), nullable=False),
                sa.Column('user_id', sa.Integer(), nullable=False),
                sa.ForeignKeyConstraint(
                    ['user_id'],
                    ['user.id'],
                ),
                sa.PrimaryKeyConstraint('id'),
            )

        if 'maintenance_event_instance' not in tableNames:
            op.create_table(
                'maintenance_event',
                sa.Column('id', sa.Integer(), nullable=False),
                sa.Column('event_date', sa.DateTime(), nullable=False),
                sa.Column('maintenance_id', sa.Integer(), nullable=False),
                sa.ForeignKeyConstraint(
                    ['maintenance_id'],
                    ['maintenance.id'],
                ),
                sa.PrimaryKeyConstraint('id'),
            )

        connection = op.get_bind()
        rows = connection.execute(text('SELECT * FROM maintenance_event;')).fetchall()

        for row in rows:
            LOGGER.debug(f'  Migrate maintenance event: {row}')
            eventId, typeName, eventDate, description, userId = row
            existingMaintenance = __get_maintenance(connection, typeName, description, userId)

            if existingMaintenance is None:
                LOGGER.debug(f'    Create new maintenance: {typeName}, {description}, {userId}')
                connection.execute(
                    text(
                        f"INSERT INTO maintenance (type, description, user_id, is_reminder_active, reminder_limit) VALUES ('{typeName}', '{description}', {userId}, False, NULL);"
                    )
                )
                existingMaintenance = __get_maintenance(connection, typeName, description, userId)

            connection.execute(
                text(
                    f"INSERT INTO maintenance_event_instance (event_date, maintenance_id) VALUES ('{eventDate}', {existingMaintenance[0]});"
                )
            )

    op.drop_table('maintenance_event')


def downgrade():
    op.drop_table('maintenance_event')
    op.drop_table('maintenance')
