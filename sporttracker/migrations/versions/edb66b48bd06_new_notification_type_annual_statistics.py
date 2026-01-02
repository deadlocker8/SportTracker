"""new_notification_type_annual_statistics

Revision ID: edb66b48bd06
Revises: 4a7f81133876
Create Date: 2026-01-02 10:50:47.567823

"""

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'edb66b48bd06'
down_revision = '4a7f81133876'
branch_labels = None
depends_on = None


def upgrade():
    if not __has_enum_value('notificationtype', 'ANNUAL_ACHIEVEMENTS_REMINDER'):
        op.execute("ALTER TYPE notificationtype ADD VALUE 'ANNUAL_ACHIEVEMENTS_REMINDER'")


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
