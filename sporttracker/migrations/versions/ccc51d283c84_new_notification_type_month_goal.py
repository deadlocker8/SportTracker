"""new_notification_type_month_goal

Revision ID: ccc51d283c84
Revises: ad4be25c855b
Create Date: 2025-08-25 22:31:05.761227

"""

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'ccc51d283c84'
down_revision = 'ad4be25c855b'
branch_labels = None
depends_on = None


def upgrade():
    if not __has_enum_value('notificationtype', 'MONTH_GOAL_DISTANCE'):
        op.execute("ALTER TYPE notificationtype ADD VALUE 'MONTH_GOAL_DISTANCE'")

    if not __has_enum_value('notificationtype', 'MONTH_GOAL_COUNT'):
        op.execute("ALTER TYPE notificationtype ADD VALUE 'MONTH_GOAL_COUNT'")

    if not __has_enum_value('notificationtype', 'MONTH_GOAL_DURATION'):
        op.execute("ALTER TYPE notificationtype ADD VALUE 'MONTH_GOAL_DURATION'")


def downgrade():
    pass


def __has_enum_value(enum_name: str, enum_value: str) -> bool:
    return (
        op.get_bind()
        .execute(
            text(f"""
                 SELECT e.enumlabel
                 FROM pg_enum e
                          JOIN pg_type t ON e.enumtypid = t.oid
                 WHERE t.typname = '{enum_name}'
                   AND e.enumlabel = '{enum_value}'
                 """)
        )
        .fetchone()
    ) is not None
