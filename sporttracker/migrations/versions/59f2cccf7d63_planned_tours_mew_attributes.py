"""planned_tours_mew_attributes

Revision ID: 59f2cccf7d63
Revises: 4eebb86b3c7f
Create Date: 2024-04-29 20:49:10.161647

"""

from datetime import datetime

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Inspector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '59f2cccf7d63'
down_revision = '4eebb86b3c7f'
branch_labels = None
depends_on = None


def upgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    columns = inspector.get_columns('planned_tour')
    columnNames = [column['name'] for column in columns]

    if 'arrival_method' not in columnNames:
        op.add_column(
            'planned_tour',
            sa.Column(
                'arrival_method',
                postgresql.ENUM(name='traveltype', create_type=False),
                nullable=True,
                default='NONE',
            ),
        )

    op.execute("UPDATE planned_tour SET arrival_method='NONE' WHERE arrival_method IS NULL;")

    if 'departure_method' not in columnNames:
        op.add_column(
            'planned_tour',
            sa.Column(
                'departure_method',
                postgresql.ENUM(name='traveltype', create_type=False),
                nullable=True,
                default='NONE',
            ),
        )

    op.execute("UPDATE planned_tour SET departure_method='NONE' WHERE departure_method IS NULL;")

    if 'direction' not in columnNames:
        op.add_column(
            'planned_tour',
            sa.Column(
                'direction',
                postgresql.ENUM(name='traveldirection', create_type=False),
                nullable=True,
                default='SINGLE',
            ),
        )

    op.execute("UPDATE planned_tour SET direction='SINGLE' WHERE direction IS NULL;")

    if 'creation_date' not in columnNames:
        op.add_column(
            'planned_tour',
            sa.Column('creation_date', sa.DateTime(), nullable=True),
        )

    op.execute('UPDATE planned_tour SET creation_date=last_edit_date WHERE creation_date IS NULL;')

    if 'last_edit_user_id' not in columnNames:
        op.add_column(
            'planned_tour',
            sa.Column('last_edit_user_id', sa.Integer(), nullable=True),
        )

    op.execute('UPDATE planned_tour SET last_edit_user_id=user_id WHERE last_edit_user_id IS NULL;')

    if 'planned_tours_last_viewed_date' not in columnNames:
        op.add_column(
            'user',
            sa.Column('planned_tours_last_viewed_date', sa.DateTime(), nullable=True),
        )

    op.execute(
        f'UPDATE "user" SET planned_tours_last_viewed_date=\'{datetime.now().isoformat()}\' WHERE planned_tours_last_viewed_date IS NULL;'
    )


def downgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    columnNames = inspector.get_columns('planned_tour')

    if 'arrival_method' in columnNames:
        op.drop_column('planned_tour', 'arrival_method')

    if 'departure_method' in columnNames:
        op.drop_column('planned_tour', 'departure_method')

    if 'direction' in columnNames:
        op.drop_column('planned_tour', 'direction')

    if 'creation_date' in columnNames:
        op.drop_column('planned_tour', 'creation_date')

    if 'last_edit_user_id' in columnNames:
        op.drop_column('planned_tour', 'last_edit_user_id')

    if 'planned_tours_last_viewed_date' in columnNames:
        op.drop_column('user', 'planned_tours_last_viewed_date')
