"""persisted_notifications

Revision ID: aa7bcf26fc75
Revises: 885a4670527a
Create Date: 2025-08-11 21:05:01.656418

"""

from datetime import datetime

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Inspector

# revision identifiers, used by Alembic.
revision = 'aa7bcf26fc75'
down_revision = '885a4670527a'
branch_labels = None
depends_on = None


def upgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    tableNames = inspector.get_table_names()

    if 'notification' not in tableNames:
        op.create_table(
            'notification',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('date_time', sa.DateTime(), nullable=False),
            sa.Column('message', sa.String(), nullable=False),
            sa.Column('message_details', sa.String(), nullable=True),
            sa.Column(
                'type',
                sa.Enum(
                    'MAINTENANCE_REMINDER',
                    'NEW_SHARED_PLANNED_TOUR',
                    'EDITED_SHARED_PLANNED_TOUR',
                    'DELETED_SHARED_PLANNED_TOUR',
                    'REVOKED_SHARED_PLANNED_TOUR',
                    'NEW_SHARED_LONG_DISTANCE_TOUR',
                    'EDITED_SHARED_LONG_DISTANCE_TOUR',
                    'DELETED_SHARED_LONG_DISTANCE_TOUR',
                    'REVOKED_SHARED_LONG_DISTANCE_TOUR',
                    name='notificationtype',
                ),
                key='type',
                name='type',
                nullable=False,
            ),
            sa.Column('item_id', sa.Integer(), nullable=True),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(
                ['user_id'],
                ['user.id'],
            ),
            sa.PrimaryKeyConstraint('id'),
        )

    inspector = Inspector.from_engine(op.get_bind().engine)
    columns = inspector.get_columns('user')
    columnNames = [column['name'] for column in columns]
    if 'long_distance_tours_last_viewed_date' in columnNames:
        op.drop_column('user', 'long_distance_tours_last_viewed_date')
    if 'planned_tours_last_viewed_date' in columnNames:
        op.drop_column('user', 'planned_tours_last_viewed_date')


def downgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    tableNames = inspector.get_table_names()

    if 'notification' in tableNames:
        op.drop_table('notification')

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

    if 'planned_tours_last_viewed_date' not in columnNames:
        op.add_column(
            'user',
            sa.Column('planned_tours_last_viewed_date', sa.DateTime(), nullable=True),
        )
        op.execute(
            f'UPDATE "user" SET planned_tours_last_viewed_date=\'{datetime.now().isoformat()}\' WHERE planned_tours_last_viewed_date IS NULL;'
        )
