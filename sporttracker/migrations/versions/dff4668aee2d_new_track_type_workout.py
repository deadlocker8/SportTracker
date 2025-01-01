"""new_track_type_workout

Revision ID: dff4668aee2d
Revises: 865b89d7e72d
Create Date: 2025-01-01 15:03:24.461704

"""

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'dff4668aee2d'
down_revision = '865b89d7e72d'
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    rows = connection.execute(text('SELECT unnest(enum_range(NULL::tracktype))::text;')).fetchall()
    existingEnumValues = [r[0] for r in rows]

    if 'WORKOUT' not in existingEnumValues:
        op.execute("ALTER TYPE tracktype ADD VALUE 'WORKOUT'")


def downgrade():
    pass
