"""track_link_planned_tour

Revision ID: ab4a46725629
Revises: 1ae2e5b3f378
Create Date: 2024-08-04 11:07:28.662544

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Inspector

# revision identifiers, used by Alembic.
revision = 'ab4a46725629'
down_revision = '1ae2e5b3f378'
branch_labels = None
depends_on = None


def upgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    tableNames = inspector.get_table_names()

    if 'track_planned_tour_association' not in tableNames:
        op.create_table(
            'track_planned_tour_association',
            sa.Column('track_id', sa.Integer(), nullable=True),
            sa.Column('planned_tour_id', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(
                ['planned_tour_id'],
                ['planned_tour_id.id'],
            ),
            sa.ForeignKeyConstraint(
                ['track_id'],
                ['track.id'],
            ),
        )


def downgrade():
    op.drop_table('track_planned_tour_association')
