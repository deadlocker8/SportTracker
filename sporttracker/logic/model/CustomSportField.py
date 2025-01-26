import enum

from flask_babel import gettext
from flask_login import current_user
from sqlalchemy import Integer, String, Boolean
from sqlalchemy.orm import mapped_column, Mapped

from sporttracker.logic.model.WorkoutType import WorkoutType
from sporttracker.logic.model.db import db


class CustomSportFieldType(enum.Enum):
    STRING = 'STRING'
    INTEGER = 'INTEGER'
    FLOAT = 'FLOAT'

    localization_key: str

    def __new__(cls, name: str):
        member = object.__new__(cls)
        member._value_ = name
        return member

    def get_localized_name(self) -> str:
        # must be done this way to include translations in *.po and *.mo file
        if self == self.STRING:
            return gettext('String')
        elif self == self.INTEGER:
            return gettext('Integer')
        elif self == self.FLOAT:
            return gettext('Float')

        raise ValueError(
            f'Could not get localized name for unsupported CustomSportFieldType: {self}'
        )


class CustomSportField(db.Model):  # type: ignore[name-defined]
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type = db.Column(db.Enum(CustomSportFieldType))
    sport_type = db.Column(db.Enum(WorkoutType))
    name: Mapped[String] = mapped_column(String, nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def get_escaped_name(self):
        return ''.join([c if c.isalnum() else '_' for c in str(self.name)])

    def __repr__(self):
        return (
            f'CustomSportField('
            f'id: {self.id}, '
            f'type: {self.type}, '
            f'sport_type: {self.sport_type}, '
            f'name: {self.name}, '
            f'is_required: {self.is_required}, '
            f'user_id: {self.user_id})'
        )


def get_custom_fields_by_sport_type(
    workoutTypes: list[WorkoutType] | None = None,
) -> dict[WorkoutType, list[CustomSportField]]:
    if workoutTypes is None:
        workoutTypes = [s for s in WorkoutType]

    customFieldsByWorkoutType = {}
    for workoutType in workoutTypes:
        customFieldsByWorkoutType[workoutType] = (
            CustomSportField.query.filter(CustomSportField.user_id == current_user.id)
            .filter(CustomSportField.sport_type == workoutType)
            .all()
        )
    return customFieldsByWorkoutType


# List of reserved names that are not allowed to be used as custom field names.
# Otherwise, the HTML form would include multiple inputs with the same name leading to unexpected behaviour.
# The actual inputs will be prefixed with "sport-" in the HTML form.
RESERVED_FIELD_NAMES = [
    'type' 'name',
    'date',
    'time',
    'distance',
    'duration-hours',
    'duration-minutes',
    'duration-seconds',
    'averageHeartRate',
    'elevationSum',
    'gpxFileName',
    'participants',
    'shareCode' 'workoutType',
    'workoutCategories',
]
