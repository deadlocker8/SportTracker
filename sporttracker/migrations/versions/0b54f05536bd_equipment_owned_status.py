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
        op.execute('ALTER TABLE "equipment" ALTER COLUMN "is_owned" SET NOT NULL;;')


def downgrade():
    pass
