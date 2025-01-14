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
    )
    LEGS = (
        'LEGS',
        'femur_alt',
        1,
    )
    CORE = (
        'CORE',
        'adjust',
        2,
    )
    YOGA = (
        'YOGA',
        'self_improvement',
        3,
    )

    icon: str
    order: int

    def __new__(
        cls,
        name: str,
        icon: str,
        order: int,
    ):
        member = object.__new__(cls)
        member._value_ = name
        member.icon = icon
        member.order = order
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
