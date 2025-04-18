"""user_tile_hunting_settings

Revision ID: 852bd10a0273
Revises: afe94400768e
Create Date: 2024-09-11 22:53:15.922798

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Inspector

# revision identifiers, used by Alembic.
revision = '852bd10a0273'
down_revision = 'afe94400768e'
branch_labels = None
depends_on = None


def upgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    columns = inspector.get_columns('user')
    columnNames = [column['name'] for column in columns]

    if 'isTileHuntingActivated' not in columnNames:
        op.add_column('user', sa.Column('isTileHuntingActivated', sa.Boolean(), nullable=True, default=True))

    op.execute('UPDATE "user" SET "isTileHuntingActivated"=True WHERE "user"."isTileHuntingActivated" IS NULL;')


def downgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    columnNames = inspector.get_columns('user')

    if 'isTileHuntingActivated' in columnNames:
        op.drop_column('user', 'isTileHuntingActivated')
