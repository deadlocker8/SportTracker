import sqlalchemy as sa
from alembic import op
from sqlalchemy import Inspector

revision = '0b54f05536bd'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)

    columns = inspector.get_columns('equipment')
    columnNames = [column['name'] for column in columns]
    if 'is_owned' not in columnNames:
        op.add_column(
            'equipment',
            sa.Column('is_owned', sa.Boolean(), nullable=True),
        )
        op.execute('UPDATE "equipment" SET "is_owned"=TRUE WHERE "equipment"."is_owned" IS NULL;')
        op.execute('ALTER TABLE "equipment" ALTER COLUMN "is_owned" SET NOT NULL;')

    columns = inspector.get_columns('filter_state_equipment')
    columnNames = [column['name'] for column in columns]
    if 'is_owned_selected' not in columnNames:
        op.add_column(
            'filter_state_equipment',
            sa.Column('is_owned_selected', sa.Boolean(), nullable=True),
        )
        op.execute(
            'UPDATE "filter_state_equipment" SET "is_owned_selected"=TRUE WHERE "filter_state_equipment"."is_owned_selected" IS NULL;'
        )
        op.execute('ALTER TABLE "filter_state_equipment" ALTER COLUMN "is_owned_selected" SET NOT NULL;')

    if 'is_not_owned_selected' not in columnNames:
        op.add_column(
            'filter_state_equipment',
            sa.Column('is_not_owned_selected', sa.Boolean(), nullable=True),
        )
        op.execute(
            'UPDATE "filter_state_equipment" SET "is_not_owned_selected"=TRUE WHERE "filter_state_equipment"."is_not_owned_selected" IS NULL;'
        )
        op.execute('ALTER TABLE "filter_state_equipment" ALTER COLUMN "is_not_owned_selected" SET NOT NULL;')


def downgrade():
    pass
