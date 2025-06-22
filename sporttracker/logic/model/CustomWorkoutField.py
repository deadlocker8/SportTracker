import enum
from dataclasses import dataclass
from operator import attrgetter

import natsort
from flask_babel import gettext
from flask_login import current_user
from natsort import natsorted
from sqlalchemy import Integer, String, Boolean
from sqlalchemy.orm import mapped_column, Mapped

from sporttracker.logic.model.Workout import Workout
from sporttracker.logic.model.WorkoutType import WorkoutType
from sporttracker.logic.model.db import db


class CustomWorkoutFieldType(enum.Enum):
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

        raise ValueError(f'Could not get localized name for unsupported CustomWorkoutFieldType: {self}')


class CustomWorkoutField(db.Model):  # type: ignore[name-defined]
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type = db.Column(db.Enum(CustomWorkoutFieldType))
    workout_type = db.Column(db.Enum(WorkoutType))
    name: Mapped[String] = mapped_column(String, nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def get_escaped_name(self):
        return ''.join([c if c.isalnum() else '_' for c in str(self.name)])

    def __repr__(self):
        return (
            f'CustomWorkoutField('
            f'id: {self.id}, '
            f'type: {self.type}, '
            f'workout_type: {self.workout_type}, '
            f'name: {self.name}, '
            f'is_required: {self.is_required}, '
            f'user_id: {self.user_id})'
        )


def get_custom_fields_grouped_by_workout_types(
    workoutTypes: list[WorkoutType] | None = None,
) -> dict[WorkoutType, list[CustomWorkoutField]]:
    if workoutTypes is None:
        workoutTypes = [s for s in WorkoutType]

    customFieldsByWorkoutType = {}
    for workoutType in workoutTypes:
        fields = (
            CustomWorkoutField.query.filter(CustomWorkoutField.user_id == current_user.id)
            .filter(CustomWorkoutField.workout_type == workoutType)
            .all()
        )
        fields = natsorted(fields, alg=natsort.ns.IGNORECASE, key=lambda field: field.name)
        customFieldsByWorkoutType[workoutType] = fields
    return customFieldsByWorkoutType


def get_custom_fields_by_workout_type(workoutType: WorkoutType) -> list[CustomWorkoutField]:
    fields = (
        CustomWorkoutField.query.filter(CustomWorkoutField.user_id == current_user.id)
        .filter(CustomWorkoutField.workout_type == workoutType)
        .all()
    )
    return natsorted(fields, alg=natsort.ns.IGNORECASE, key=attrgetter('name'))


def get_custom_field_by_id(customFieldId: int) -> CustomWorkoutField | None:
    return (
        CustomWorkoutField.query.filter(CustomWorkoutField.user_id == current_user.id)
        .filter(CustomWorkoutField.id == customFieldId)
        .first()
    )


@dataclass
class CustomWorkoutFieldWithValues:
    custom_field: CustomWorkoutField
    values: list[str | int | float]


def get_custom_fields_grouped_by_workout_types_wih_values() -> dict[WorkoutType, list[CustomWorkoutFieldWithValues]]:
    customFieldsByWorkoutType = {}
    for workoutType in [s for s in WorkoutType]:
        fields = (
            CustomWorkoutField.query.filter(CustomWorkoutField.user_id == current_user.id)
            .filter(CustomWorkoutField.workout_type == workoutType)
            .all()
        )
        fields = natsorted(fields, alg=natsort.ns.IGNORECASE, key=lambda f: f.name)

        fieldsWithValues = []
        for field in fields:
            fieldsWithValues.append(__get_custom_field_with_values(field))

        customFieldsByWorkoutType[workoutType] = fieldsWithValues
    return customFieldsByWorkoutType


def __get_custom_field_with_values(customField: CustomWorkoutField) -> CustomWorkoutFieldWithValues:
    customFieldOperator = Workout.custom_fields[customField.name].astext.cast(String)

    rows = (
        Workout.query.with_entities(customFieldOperator)
        .filter(Workout.user_id == current_user.id)
        .filter(Workout.type == customField.workout_type)
        .group_by(customFieldOperator)
        .all()
    )

    values = [row[0] for row in rows if row[0] is not None]

    return CustomWorkoutFieldWithValues(customField, natsorted(values, alg=natsort.ns.IGNORECASE))


# List of reserved names that are not allowed to be used as custom field names.
# Otherwise, the HTML form would include multiple inputs with the same name leading to unexpected behaviour.
RESERVED_FIELD_NAMES = [
    'type',
    'name',
    'date',
    'time',
    'distance',
    'duration_hours',
    'duration_minutes',
    'duration_seconds',
    'average_heart_rate',
    'elevation_Sum',
    'gpx_file_name',
    'participants',
    'share_code',
    'fitness_workout_type',
    'fitness_workout_categories',
    'planned_tour_id',
    'is_import_from_fit_file',
]
