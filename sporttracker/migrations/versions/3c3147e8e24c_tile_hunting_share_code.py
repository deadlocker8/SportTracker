"""tile_hunting_share_code

Revision ID: 3c3147e8e24c
Revises: 4439c9dfc7c7
Create Date: 2024-11-08 23:00:10.740574

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Inspector

# revision identifiers, used by Alembic.
revision = '3c3147e8e24c'
down_revision = '4439c9dfc7c7'
branch_labels = None
depends_on = None


def upgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    columns = inspector.get_columns('user')
    columnNames = [column['name'] for column in columns]

    if 'isTileHuntingAccessActivated' not in columnNames:
        op.add_column(
            'user',
            sa.Column('isTileHuntingAccessActivated', sa.Boolean(), nullable=True, default=True),
        )

    op.execute(
        'UPDATE "user" SET "isTileHuntingAccessActivated"=False WHERE "user"."isTileHuntingAccessActivated" IS NULL;'
    )

    if 'tileHuntingShareCode' not in columnNames:
        op.add_column('user', sa.Column('tileHuntingShareCode', sa.String(), nullable=True, default=None))


def downgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    columnNames = inspector.get_columns('user')

    if 'isTileHuntingAccessActivated' in columnNames:
        op.drop_column('user', 'isTileHuntingAccessActivated')

    if 'tileHuntingShareCode' in columnNames:
        op.drop_column('user', 'tileHuntingShareCode')
