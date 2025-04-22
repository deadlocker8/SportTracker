"""fix_planned_tour_share_codes

Revision ID: ad3012342146
Revises: 903e7e388131
Create Date: 2025-04-22 23:27:53.653259

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = 'ad3012342146'
down_revision = '903e7e388131'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('UPDATE "planned_tour" SET "share_code"=NULL WHERE "planned_tour"."share_code" =\'\';')


def downgrade():
    pass
