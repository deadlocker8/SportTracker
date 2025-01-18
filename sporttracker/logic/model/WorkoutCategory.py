import enum

from flask_babel import gettext
from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from sporttracker.logic.model.db import db


class WorkoutCategoryType(enum.Enum):
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

        raise ValueError(
            f'Could not get localized name for unsupported WorkoutCategoryType: {self}'
        )


class WorkoutCategory(db.Model):  # type: ignore[name-defined]
    track_id: Mapped[int] = mapped_column(Integer, nullable=False, primary_key=True)
    workout_category_type = db.Column(
        db.Enum(WorkoutCategoryType), nullable=False, primary_key=True
    )


def update_workout_categories_by_track_id(
    trackId: int, newWorkoutCategories: list[WorkoutCategoryType]
) -> None:
    WorkoutCategory.query.filter(WorkoutCategory.track_id == trackId).delete()

    for category in newWorkoutCategories:
        db.session.add(WorkoutCategory(track_id=trackId, workout_category_type=category))

    db.session.commit()
