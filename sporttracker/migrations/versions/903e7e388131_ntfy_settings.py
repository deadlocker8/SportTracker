"""ntfy_settings

Revision ID: 903e7e388131
Revises: ab63039e89ac
Create Date: 2025-02-26 21:58:26.709107

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Inspector

# revision identifiers, used by Alembic.
revision = '903e7e388131'
down_revision = 'ab63039e89ac'
branch_labels = None
depends_on = None


def upgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    columns = inspector.get_columns('user')
    columnNames = [column['name'] for column in columns]
    tableNames = inspector.get_table_names()

    if 'isMaintenanceRemindersNotificationsActivated' not in columnNames:
        op.add_column(
            'user',
            sa.Column(
                'isMaintenanceRemindersNotificationsActivated',
                sa.Boolean(),
                nullable=True,
                default=True,
            ),
        )

    op.execute(
        'UPDATE "user" SET "isMaintenanceRemindersNotificationsActivated"=False WHERE "user"."isMaintenanceRemindersNotificationsActivated" IS NULL;'
    )

    if 'ntfy_settings' not in tableNames:
        op.create_table(
            'ntfy_settings',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('username', sa.String(), nullable=False),
            sa.Column('password', sa.String(), nullable=False),
            sa.Column('server_url', sa.String(), nullable=False),
            sa.Column('topic', sa.String(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(
                ['user_id'],
                ['user.id'],
            ),
            sa.PrimaryKeyConstraint('id'),
        )


def downgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    columnNames = inspector.get_columns('user')
    tableNames = inspector.get_table_names()

    if 'isMaintenanceRemindersNotificationsActivated' in columnNames:
        op.drop_column('user', 'isMaintenanceRemindersNotificationsActivated')

    if 'ntfy_settings' in tableNames:
        op.drop_table('planned_tour')
