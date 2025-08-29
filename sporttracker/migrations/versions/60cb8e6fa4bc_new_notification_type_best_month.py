"""new_notification_type_best_month

Revision ID: 60cb8e6fa4bc
Revises: ccc51d283c84
Create Date: 2025-08-29 22:46:11.928506

"""

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '60cb8e6fa4bc'
down_revision = 'ccc51d283c84'
branch_labels = None
depends_on = None


def upgrade():
    if not __has_enum_value('notificationtype', 'BEST_MONTH'):
        op.execute("ALTER TYPE notificationtype ADD VALUE 'BEST_MONTH'")


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
