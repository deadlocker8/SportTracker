"""planned_tours_creation_date

Revision ID: 772f84a6f268
Revises: 7cac13f41c7e
Create Date: 2024-04-30 17:52:10.638148

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Inspector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '772f84a6f268'
down_revision = '7cac13f41c7e'
branch_labels = None
depends_on = None


def upgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    columns = inspector.get_columns('planned_tour')
    columnNames = [column['name'] for column in columns]

    if 'creation_date' not in columnNames:
        op.add_column(
            'planned_tour',
            sa.Column('creation_date', sa.DateTime(), nullable=True),
        )

    op.execute("UPDATE planned_tour SET creation_date=last_edit_date WHERE creation_date IS NULL;")

    if 'last_edit_user_id' not in columnNames:
        op.add_column(
            'planned_tour',
            sa.Column('last_edit_user_id', sa.Integer(), nullable=True),
        )

    op.execute("UPDATE planned_tour SET last_edit_user_id=user_id WHERE last_edit_user_id IS NULL;")


def downgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    columnNames = inspector.get_columns('planned_tour')

    if 'creation_date' in columnNames:
        op.drop_column('planned_tour', 'creation_date')

    if 'last_edit_user_id' in columnNames:
        op.drop_column('planned_tour', 'last_edit_user_id')
