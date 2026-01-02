"""quick_filter_state_years

Revision ID: 26147b33db44
Revises: edb66b48bd06
Create Date: 2026-01-02 12:44:47.800377

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = '26147b33db44'
down_revision = 'edb66b48bd06'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("UPDATE filter_state_quick SET years='{}';")


def downgrade():
    pass
