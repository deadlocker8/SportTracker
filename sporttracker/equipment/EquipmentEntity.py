from datetime import date
from typing import ClassVar

from sqlalchemy import Column, Date, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column

from sporttracker.db import db
from sporttracker.helpers import DateFormats
from sporttracker.workout.WorkoutType import WorkoutType


class Equipment(db.Model):  # type: ignore[name-defined]
    __tablename__ = 'equipment'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    class_type = db.Column(db.String)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    workout_type = db.Column(db.Enum(WorkoutType))
    name: Mapped[str] = mapped_column(String, nullable=False)
    purchase_date: Mapped[date] = mapped_column(Date, nullable=True)
    is_active = db.Column(db.Boolean(), nullable=False)
    inactive_date: Mapped[date] = mapped_column(Date, nullable=True)

    __mapper_args__: ClassVar[dict[str, str]] = {
        'polymorphic_identity': 'equipment',
        'polymorphic_on': 'class_type',
    }

    def get_date(self) -> str:
        return self.datetime.strftime(DateFormats.DATE_FORMAT_DATE)

    @staticmethod
    def get_icon() -> tuple[str, bool]:
        """
        Returns the icon and a bool stating whether icon is a font-awesome icon
        :return:
        """
        return 'apparel', False

    def __repr__(self):
        return (
            f'Equipment('
            f'id: {self.id}, '
            f'user_id: {self.user_id}, '
            f'workout_type: {self.workout_type}, '
            f'name: {self.name}, '
            f'purchase_date: {self.purchase_date}, '
            f'is_active: {self.is_active}, '
            f'inactive_date: {self.inactive_date})'
        )


workout_equipment_association = Table(
    'workout_equipment_association',
    db.Model.metadata,
    Column('workout_id', ForeignKey('workout.id', ondelete='CASCADE')),
    Column('equipment_id', ForeignKey('equipment.id', ondelete='CASCADE')),
)
