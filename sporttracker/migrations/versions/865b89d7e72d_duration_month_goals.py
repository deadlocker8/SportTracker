"""duration_month_goals

Revision ID: 865b89d7e72d
Revises: 32a559e9dc12
Create Date: 2024-12-31 17:19:41.475746

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Inspector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '865b89d7e72d'
down_revision = '32a559e9dc12'
branch_labels = None
depends_on = None


def __get_table_names() -> list[str]:
    inspector = Inspector.from_engine(op.get_bind().engine)
    return inspector.get_table_names()


def upgrade():
    tableNames = __get_table_names()

    if 'month_goal_duration' not in tableNames:
        op.create_table(
            'month_goal_duration',
            sa.Column('duration_minimum', sa.Integer(), nullable=False),
            sa.Column('duration_perfect', sa.Integer(), nullable=False),
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('type', postgresql.ENUM(name='tracktype', create_type=False), nullable=True),
            sa.Column('year', sa.Integer(), nullable=False),
            sa.Column('month', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(
                ['user_id'],
                ['user.id'],
            ),
            sa.PrimaryKeyConstraint('id'),
        )


def downgrade():
    tableNames = __get_table_names()

    if 'month_goal_duration' in tableNames:
        op.drop_table('month_goal_duration')
