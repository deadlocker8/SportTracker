import sqlalchemy as sa
from alembic import op
from sqlalchemy import Inspector
from sqlalchemy.dialects import postgresql

revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def __get_table_names() -> list[str]:
    inspector = Inspector.from_engine(op.get_bind().engine)
    return inspector.get_table_names()


def upgrade():
    tableNames = __get_table_names()

    if 'equipment_preset' not in tableNames:
        op.create_table(
            'equipment_preset',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column(
                'workout_type',
                postgresql.ENUM(name='workouttype', create_type=False),
                nullable=False,
            ),
            sa.Column('name', sa.String(), nullable=False),
            sa.ForeignKeyConstraint(
                ['user_id'],
                ['user.id'],
                ondelete='CASCADE',
            ),
            sa.PrimaryKeyConstraint('id'),
        )

    if 'equipment_preset_equipment_association' not in tableNames:
        op.create_table(
            'equipment_preset_equipment_association',
            sa.Column('equipment_preset_id', sa.Integer(), nullable=False),
            sa.Column('equipment_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(
                ['equipment_preset_id'],
                ['equipment_preset.id'],
                ondelete='CASCADE',
            ),
            sa.ForeignKeyConstraint(
                ['equipment_id'],
                ['equipment.id'],
                ondelete='CASCADE',
            ),
        )


def downgrade():
    tableNames = __get_table_names()

    if 'equipment_preset_equipment_association' in tableNames:
        op.drop_table('equipment_preset_equipment_association')

    if 'equipment_preset' in tableNames:
        op.drop_table('equipment_preset')
