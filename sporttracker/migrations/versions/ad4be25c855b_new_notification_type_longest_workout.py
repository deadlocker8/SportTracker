"""new_notification_type_longest_workout

Revision ID: ad4be25c855b
Revises: 1f317da032a0
Create Date: 2025-08-24 22:58:15.063853

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = 'ad4be25c855b'
down_revision = '1f317da032a0'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TYPE notificationtype ADD VALUE 'LONGEST_WORKOUT'")


def downgrade():
    pass
