import sqlalchemy as sa
from alembic import op
from sqlalchemy import Inspector

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '9c1d7e4b6a2f'
branch_labels = None
depends_on = None


def __get_column_names(table_name: str) -> list[str]:
    inspector = Inspector.from_engine(op.get_bind().engine)
    return [column['name'] for column in inspector.get_columns(table_name)]


def upgrade():
    columnNames = __get_column_names('maintenance')

    if 'equipment_id' not in columnNames:
        op.add_column('maintenance', sa.Column('equipment_id', sa.Integer(), nullable=True))
        op.create_foreign_key(None, 'maintenance', 'equipment', ['equipment_id'], ['id'], ondelete='SET NULL')


def downgrade():
    columnNames = __get_column_names('maintenance')

    if 'equipment_id' in columnNames:
        op.drop_column('maintenance', 'equipment_id')
