"""notification_settings

Revision ID: 1f317da032a0
Revises: aa7bcf26fc75
Create Date: 2025-08-17 14:51:28.733389

"""

import json

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Inspector, text
from sqlalchemy.dialects import postgresql

from sporttracker.logic.model.NotificationType import NotificationType

# revision identifiers, used by Alembic.
revision = '1f317da032a0'
down_revision = 'aa7bcf26fc75'
branch_labels = None
depends_on = None


def upgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    tableNames = inspector.get_table_names()

    if 'notification_settings' not in tableNames:
        op.create_table(
            'notification_settings',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column(
                'provider_type',
                sa.Enum(
                    'NTFY',
                    name='notificationprovidertype',
                ),
                nullable=False,
            ),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('notification_types', postgresql.JSON(astext_type=sa.Text()), nullable=True),
            sa.ForeignKeyConstraint(
                ['user_id'],
                ['user.id'],
            ),
            sa.PrimaryKeyConstraint('id'),
        )

    connection = op.get_bind()
    existingRows = connection.execute(text('SELECT * FROM notification_settings;')).fetchall()
    if not existingRows:
        userRows = connection.execute(
            text('SELECT "user".id, "user"."isMaintenanceRemindersNotificationsActivated" FROM "user";')
        ).fetchall()

        notificationTypes = json.dumps({notificationType.name: True for notificationType in NotificationType})

        for row in userRows:
            userId, isMaintenanceRemindersNotificationsActivated = row
            connection.execute(
                text(
                    f'INSERT INTO notification_settings (provider_type, user_id, is_active, notification_types) '
                    f"VALUES ('NTFY', {userId}, {isMaintenanceRemindersNotificationsActivated}, '{notificationTypes}');"
                )
            )

    columns = inspector.get_columns('user')
    columnNames = [column['name'] for column in columns]
    if 'isMaintenanceRemindersNotificationsActivated' in columnNames:
        op.drop_column('user', 'isMaintenanceRemindersNotificationsActivated')


def downgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    tableNames = inspector.get_table_names()

    if 'notification_settings' in tableNames:
        op.drop_table('notification_settings')
