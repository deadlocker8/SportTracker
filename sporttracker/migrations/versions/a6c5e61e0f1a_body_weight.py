"""body_weight

Revision ID: a6c5e61e0f1a
Revises: 26147b33db44
Create Date: 2026-08-01 16:32:36.573057

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Inspector

# revision identifiers, used by Alembic.
revision = 'a6c5e61e0f1a'
down_revision = '26147b33db44'
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

    if 'body_weight' not in tableNames:
        op.create_table(
            'body_weight',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('datetime', sa.DateTime(), nullable=False),
            sa.Column('weight', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(
                ['user_id'],
                ['user.id'],
            ),
            sa.PrimaryKeyConstraint('id'),
        )


def downgrade():
    tableNames = __get_table_names()
    if 'body_weight' in tableNames:
        op.drop_table('body_weight')
