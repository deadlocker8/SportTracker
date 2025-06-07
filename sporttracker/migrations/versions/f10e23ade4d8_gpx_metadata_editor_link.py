"""gpx_metadata_editor_link

Revision ID: f10e23ade4d8
Revises: 42608807ae69
Create Date: 2025-06-07 17:20:13.683117

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Inspector

# revision identifiers, used by Alembic.
revision = 'f10e23ade4d8'
down_revision = '42608807ae69'
branch_labels = None
depends_on = None


def upgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    columns = inspector.get_columns('gpx_metadata')
    columnNames = [column['name'] for column in columns]

    if 'editor_link' not in columnNames:
        op.add_column(
            'gpx_metadata',
            sa.Column('editor_link', sa.String(), nullable=True),
        )


def downgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    columnNames = inspector.get_columns('gpx_metadata')

    if 'editor_link' in columnNames:
        op.drop_column('gpx_metadata', 'editor_link')
