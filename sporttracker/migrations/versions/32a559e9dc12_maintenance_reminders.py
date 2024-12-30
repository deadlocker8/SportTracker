"""maintenance_reminders

Revision ID: 32a559e9dc12
Revises: 77406774a9e6
Create Date: 2024-12-30 21:40:39.965910

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Inspector

# revision identifiers, used by Alembic.
revision = '32a559e9dc12'
down_revision = '77406774a9e6'
branch_labels = None
depends_on = None


def upgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    columns = inspector.get_columns('maintenance')
    columnNames = [column['name'] for column in columns]

    if 'is_reminder_active' not in columnNames:
        op.add_column(
            'maintenance',
            sa.Column(
                'is_reminder_active',
                sa.Boolean(),
                nullable=False,
                default=False,
            ),
        )

    op.execute('UPDATE maintenance SET is_reminder_active=False WHERE is_reminder_active IS NULL;')

    if 'reminder_limit' not in columnNames:
        op.add_column(
            'maintenance',
            sa.Column(
                'reminder_limit',
                sa.Integer(),
                nullable=False,
                default=None,
            ),
        )


def downgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    columnNames = inspector.get_columns('maintenance')

    if 'is_reminder_active' in columnNames:
        op.drop_column('maintenance', 'is_reminder_active')

    if 'reminder_limit' in columnNames:
        op.drop_column('maintenance', 'reminder_limit')
