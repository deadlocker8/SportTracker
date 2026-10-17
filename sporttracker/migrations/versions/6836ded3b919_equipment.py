"""equipment

Revision ID: 6836ded3b919
Revises: 3865d076b199
Create Date: 2026-10-17 23:32:54.625942

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Inspector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '6836ded3b919'
down_revision = '3865d076b199'
branch_labels = None
depends_on = None


def __get_table_names() -> list[str]:
    inspector = Inspector.from_engine(op.get_bind().engine)
    return inspector.get_table_names()


def __get_column_names(table_name: str) -> list[str]:
    inspector = Inspector.from_engine(op.get_bind().engine)
    return [column['name'] for column in inspector.get_columns(table_name)]


def upgrade():
    tableNames = __get_table_names()

    if 'equipment' not in tableNames:
        op.create_table(
            'equipment',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column(
                'type',
                postgresql.ENUM(name='equipmenttype', create_type=False),
                nullable=True,
                default='SINGLE',
            ),
            sa.Column(
                'workout_type',
                postgresql.ENUM(name='workouttype', create_type=False),
                nullable=False,
            ),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('purchase_date', sa.Date(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('inactive_date', sa.Date(), nullable=True),
            sa.ForeignKeyConstraint(
                ['user_id'],
                ['user.id'],
            ),
            sa.PrimaryKeyConstraint('id'),
        )


def downgrade():
    tableNames = __get_table_names()
    if 'equipment' in tableNames:
        op.drop_table('equipment')
