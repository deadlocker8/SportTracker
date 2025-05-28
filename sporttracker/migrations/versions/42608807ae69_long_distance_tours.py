"""long_distance_tours

Revision ID: 42608807ae69
Revises: ad3012342146
Create Date: 2025-05-15 21:47:45.393975

"""

from datetime import datetime

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Inspector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '42608807ae69'
down_revision = 'ad3012342146'
branch_labels = None
depends_on = None


def upgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    columns = inspector.get_columns('user')
    columnNames = [column['name'] for column in columns]

    if 'long_distance_tours_last_viewed_date' not in columnNames:
        op.add_column(
            'user',
            sa.Column('long_distance_tours_last_viewed_date', sa.DateTime(), nullable=True),
        )
        op.execute(
            f'UPDATE "user" SET "long_distance_tours_last_viewed_date" = \'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\' WHERE "user"."long_distance_tours_last_viewed_date" IS NULL;'
        )

    tableNames = inspector.get_table_names()

    if 'long_distance_tour' not in tableNames:
        op.create_table(
            'long_distance_tour',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('type', postgresql.ENUM(name='tracktype', create_type=False), nullable=True),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('last_edit_date', sa.DateTime(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('creation_date', sa.DateTime(), nullable=False),
            sa.Column('last_edit_user_id', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(
                ['user_id'],
                ['user.id'],
            ),
            sa.PrimaryKeyConstraint('id'),
        )

    if 'long_distance_tour_user_association' not in tableNames:
        op.create_table(
            'long_distance_tour_user_association',
            sa.Column('long_distance_tour_id', sa.Integer(), nullable=True),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(
                ['long_distance_tour_id'],
                ['long_distance_tour.id'],
            ),
            sa.ForeignKeyConstraint(
                ['user_id'],
                ['user.id'],
            ),
        )

    if 'long_distance_tour_planned_tour_association' not in tableNames:
        op.create_table(
            'long_distance_tour_planned_tour_association',
            sa.Column('long_distance_tour_id', sa.Integer(), nullable=False),
            sa.Column('planned_tour_id', sa.Integer(), nullable=False),
            sa.Column('order', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(
                ['long_distance_tour_id'],
                ['long_distance_tour.id'],
            ),
            sa.ForeignKeyConstraint(
                ['planned_tour_id'],
                ['planned_tour.id'],
            ),
            sa.PrimaryKeyConstraint('long_distance_tour_id', 'planned_tour_id'),
        )


def downgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    columnNames = inspector.get_columns('user')

    if 'long_distance_tours_last_viewed_date' in columnNames:
        op.drop_column('user', 'long_distance_tours_last_viewed_date')

    tableNames = inspector.get_table_names()

    if 'long_distance_tour' in tableNames:
        op.drop_table('planned_tour')

    if 'long_distance_tour_user_association' in tableNames:
        op.drop_table('long_distance_tour_user_association')
