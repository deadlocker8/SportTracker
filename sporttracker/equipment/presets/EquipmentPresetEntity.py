from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sporttracker.db import db
from sporttracker.equipment.EquipmentEntity import Equipment, equipment_preset_equipment_association
from sporttracker.workout.WorkoutType import WorkoutType


class EquipmentPreset(db.Model):  # type: ignore[name-defined]
    __tablename__ = 'equipment_preset'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    workout_type = db.Column(db.Enum(WorkoutType), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    equipment: Mapped[list[Equipment]] = relationship(
        secondary=equipment_preset_equipment_association, passive_deletes=True
    )

    def __repr__(self):
        return (
            f'EquipmentPreset('
            f'id: {self.id}, '
            f'user_id: {self.user_id}, '
            f'workout_type: {self.workout_type}, '
            f'name: {self.name}, '
            f'equipment: {[e.id for e in self.equipment]})'
        )
