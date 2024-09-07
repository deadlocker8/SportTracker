"""gpx metadata

Revision ID: 6ac8efb50f62
Revises: ab4a46725629
Create Date: 2024-09-07 15:40:24.277808

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Inspector

# revision identifiers, used by Alembic.
revision = '6ac8efb50f62'
down_revision = 'ab4a46725629'
branch_labels = None
depends_on = None


def upgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    tableNames = inspector.get_table_names()

    if 'gpx_metadata' not in tableNames:
        op.create_table(
            'gpx_metadata',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('gpx_file_name', sa.String(), nullable=False),
            sa.Column('length', sa.Float(), nullable=False),
            sa.Column('elevation_minimum', sa.Integer(), nullable=True),
            sa.Column('elevation_maximum', sa.Integer(), nullable=True),
            sa.Column('uphill', sa.Integer(), nullable=True),
            sa.Column('downhill', sa.Integer(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
        )


def downgrade():
    op.drop_table('gpx_metadata')
