"""added new track type HIKING

Revision ID: dfe516ee46da
Revises: 96da36733178
Create Date: 2024-02-12 22:08:24.165857

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = 'dfe516ee46da'
down_revision = '96da36733178'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TYPE tracktype ADD VALUE 'HIKING'")


def downgrade():
    pass
