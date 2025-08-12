"""persisted_notifications

Revision ID: aa7bcf26fc75
Revises: 885a4670527a
Create Date: 2025-08-11 21:05:01.656418

"""

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


def downgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    tableNames = inspector.get_table_names()

    if 'notification' in tableNames:
        op.drop_table('notification')
