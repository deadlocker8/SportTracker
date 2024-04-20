"""planned_tours

Revision ID: 41c4f10f2564
Revises: 1f5f7eae19c9
Create Date: 2024-04-20 11:29:40.568579

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '41c4f10f2564'
down_revision = '1f5f7eae19c9'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'planned_tour',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('type', postgresql.ENUM(name='tracktype', create_type=False), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('last_edit_date', sa.DateTime(), nullable=False),
        sa.Column('gpxFileName', sa.String(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['user.id'],
        ),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('planned_tour')
