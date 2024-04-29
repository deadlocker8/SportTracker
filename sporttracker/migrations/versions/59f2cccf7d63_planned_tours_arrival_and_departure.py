"""planned_tours_arrival_and_departure

Revision ID: 59f2cccf7d63
Revises: 4eebb86b3c7f
Create Date: 2024-04-29 20:49:10.161647

"""

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

    op.execute("UPDATE planned_tour SET arrival_method='NONE' WHERE arrival_method IS NULL;")
    op.execute("UPDATE planned_tour SET departure_method='NONE' WHERE departure_method IS NULL;")


def downgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    columnNames = inspector.get_columns('planned_tour')

    if 'arrival_method' in columnNames:
        op.drop_column('planned_tour', 'arrival_method')

    if 'departure_method' in columnNames:
        op.drop_column('planned_tour', 'departure_method')
