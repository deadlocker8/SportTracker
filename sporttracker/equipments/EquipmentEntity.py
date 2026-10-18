from datetime import date

from sqlalchemy import Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from sporttracker.db import db
from sporttracker.equipments.EquipmentType import EquipmentType
from sporttracker.helpers import DateFormats
from sporttracker.workout.WorkoutType import WorkoutType


class Equipment(db.Model):  # type: ignore[name-defined]
    __tablename__ = 'equipment'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    type = db.Column(db.Enum(EquipmentType))
    workout_type = db.Column(db.Enum(WorkoutType))
    name: Mapped[str] = mapped_column(String, nullable=False)
    purchase_date: Mapped[date] = mapped_column(Date, nullable=True)
    is_active = db.Column(db.Boolean(), nullable=False)
    inactive_date: Mapped[date] = mapped_column(Date, nullable=True)

    def get_date(self) -> str:
        return self.datetime.strftime(DateFormats.DATE_FORMAT_DATE)

    def __repr__(self):
        return (
            f'EquipmentEntity('
            f'id: {self.id}, '
            f'user_id: {self.user_id}, '
            f'type: {self.type}, '
            f'workout_type: {self.workout_type}, '
            f'name: {self.name}, '
            f'purchase_date: {self.purchase_date}, '
            f'is_active: {self.is_active}, '
            f'inactive_date: {self.inactive_date})'
        )
