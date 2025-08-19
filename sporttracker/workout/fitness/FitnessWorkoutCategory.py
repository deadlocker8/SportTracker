import enum

from flask_babel import gettext
from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from sporttracker.logic.model.db import db


class FitnessWorkoutCategoryType(enum.Enum):
    ARMS = (
        'ARMS',
        'humerus_alt',
        0,
        True,
    )
    LEGS = (
        'LEGS',
        'femur_alt',
        1,
        True,
    )
    CORE = (
        'CORE',
        'adjust',
        2,
        True,
    )
    YOGA = ('YOGA', 'self_improvement', 3, False)

    icon: str
    order: int
    is_outlined_icon: bool

    def __new__(cls, name: str, icon: str, order: int, is_outlined_icon: bool):
        member = object.__new__(cls)
        member._value_ = name
        member.icon = icon
        member.order = order
        member.is_outlined_icon = is_outlined_icon
        return member

    def get_localized_name(self) -> str:
        # must be done this way to include translations in *.po and *.mo file
        if self == self.ARMS:
            return gettext('Arms')
        elif self == self.LEGS:
            return gettext('Legs')
        elif self == self.CORE:
            return gettext('Core')
        elif self == self.YOGA:
            return gettext('Yoga')

        raise ValueError(f'Could not get localized name for unsupported FitnessWorkoutCategoryType: {self}')


class FitnessWorkoutCategory(db.Model):  # type: ignore[name-defined]
    workout_id: Mapped[int] = mapped_column(Integer, nullable=False, primary_key=True)
    fitness_workout_category_type = db.Column(db.Enum(FitnessWorkoutCategoryType), nullable=False, primary_key=True)


def update_workout_categories_by_workout_id(
    workoutId: int, newWorkoutCategories: list[FitnessWorkoutCategoryType]
) -> None:
    FitnessWorkoutCategory.query.filter(FitnessWorkoutCategory.workout_id == workoutId).delete()

    for category in newWorkoutCategories:
        db.session.add(FitnessWorkoutCategory(workout_id=workoutId, fitness_workout_category_type=category))

    db.session.commit()
