"""equipment_filter_state

Revision ID: 9c1d7e4b6a2f
Revises: 6836ded3b919
Create Date: 2026-11-04 12:00:00.000000

"""

import json

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Inspector, text
from sqlalchemy.dialects import postgresql

from sporttracker.equipment.clothes.ClothesType import ClothesType
from sporttracker.equipment.EquipmentType import EquipmentType

# revision identifiers, used by Alembic.
revision = '9c1d7e4b6a2f'
down_revision = '6836ded3b919'
branch_labels = None
depends_on = None


def upgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)

    if 'filter_state_equipment' not in inspector.get_table_names():
        op.create_table(
            'filter_state_equipment',
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('equipment_types', postgresql.JSON(astext_type=sa.Text()), nullable=True),
            sa.Column('clothes_types', postgresql.JSON(astext_type=sa.Text()), nullable=True),
            sa.Column('is_active_selected', sa.Boolean(), nullable=False),
            sa.Column('is_inactive_selected', sa.Boolean(), nullable=False),
            sa.ForeignKeyConstraint(
                ['user_id'],
                ['user.id'],
                ondelete='CASCADE',
            ),
            sa.PrimaryKeyConstraint('user_id'),
        )

    connection = op.get_bind()
    existingRows = connection.execute(text('SELECT * FROM filter_state_equipment;')).fetchall()
    if not existingRows:
        userIdRows = connection.execute(text('SELECT "user".id FROM "user";')).fetchall()

        equipmentTypes = json.dumps({equipmentType.name: True for equipmentType in EquipmentType})
        clothesTypes = json.dumps({clothesType.name: True for clothesType in ClothesType})

        for userIdRow in userIdRows:
            connection.execute(
                text(
                    'INSERT INTO filter_state_equipment (user_id, equipment_types, clothes_types, '
                    'is_active_selected, is_inactive_selected) '
                    'VALUES (:user_id, :equipment_types, :clothes_types, :is_active_selected, :is_inactive_selected);'
                ),
                {
                    'user_id': userIdRow[0],
                    'equipment_types': equipmentTypes,
                    'clothes_types': clothesTypes,
                    'is_active_selected': True,
                    'is_inactive_selected': True,
                },
            )


def downgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)

    if 'filter_state_equipment' in inspector.get_table_names():
        op.drop_table('filter_state_equipment')
