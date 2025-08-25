"""new_notification_type_longest_workout

Revision ID: ad4be25c855b
Revises: 1f317da032a0
Create Date: 2025-08-24 22:58:15.063853

"""

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'ad4be25c855b'
down_revision = '1f317da032a0'
branch_labels = None
depends_on = None


def upgrade():
    result = (
        op.get_bind()
        .execute(
            text("""
            SELECT e.enumlabel
            FROM pg_enum e
                     JOIN pg_type t ON e.enumtypid = t.oid
            WHERE t.typname = 'notificationtype'
              AND e.enumlabel = 'LONGEST_WORKOUT'
            """)
        )
        .fetchone()
    )
    if not result:
        op.execute("ALTER TYPE notificationtype ADD VALUE 'LONGEST_WORKOUT'")


def downgrade():
    pass
