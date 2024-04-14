"""maintenance_events

Revision ID: 1f5f7eae19c9
Revises: c568e6083686
Create Date: 2024-04-14 17:41:58.614132

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '1f5f7eae19c9'
down_revision = 'c568e6083686'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'maintenance_event',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('type', sa.Enum('BIKING', 'RUNNING', 'HIKING', name='tracktype'), nullable=True),
        sa.Column('event_date', sa.DateTime(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['user.id'],
        ),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('maintenance_event')
