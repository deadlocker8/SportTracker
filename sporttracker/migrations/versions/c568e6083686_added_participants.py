"""added participants

Revision ID: c568e6083686
Revises: dfe516ee46da
Create Date: 2024-02-28 22:53:21.806309

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c568e6083686'
down_revision = 'dfe516ee46da'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'participant',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['user.id'],
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'track_participant_association',
        sa.Column('track_id', sa.Integer(), nullable=True),
        sa.Column('participant_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ['participant_id'],
            ['participant.id'],
        ),
        sa.ForeignKeyConstraint(
            ['track_id'],
            ['track.id'],
        ),
    )


def downgrade():
    op.drop_table('track_participant_association')
    op.drop_table('participant')
