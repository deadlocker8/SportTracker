"""planned_tours_shareable

Revision ID: 4eebb86b3c7f
Revises: 41c4f10f2564
Create Date: 2024-04-27 20:22:09.987995

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy import Inspector

# revision identifiers, used by Alembic.
revision = '4eebb86b3c7f'
down_revision = '41c4f10f2564'
branch_labels = None
depends_on = None


def upgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    tableNames = inspector.get_table_names()

    if 'planned_tour_user_association' not in tableNames:
        op.create_table('planned_tour_user_association',
                        sa.Column('planned_tour_id', sa.Integer(), nullable=True),
                        sa.Column('user_id', sa.Integer(), nullable=True),
                        sa.ForeignKeyConstraint(['planned_tour_id'], ['planned_tour.id'], ),
                        sa.ForeignKeyConstraint(['user_id'], ['user.id'], )
                        )


def downgrade():
    op.drop_table('planned_tour_user_association')
