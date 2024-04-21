import enum

from flask_babel import gettext
from flask_login import current_user
from sqlalchemy import Integer, String, Boolean
from sqlalchemy.orm import mapped_column, Mapped

from sporttracker.logic.model.Track import TrackType
from sporttracker.logic.model.db import db


class CustomTrackFieldType(enum.Enum):
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
            f'Could not get localized name for unsupported CustomTrackFieldType: {self}'
        )


class CustomTrackField(db.Model):  # type: ignore[name-defined]
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type = db.Column(db.Enum(CustomTrackFieldType))
    track_type = db.Column(db.Enum(TrackType))
    name: Mapped[String] = mapped_column(String, nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def get_escaped_name(self):
        return ''.join([c if c.isalnum() else '_' for c in str(self.name)])

    def __repr__(self):
        return (
            f'CustomTrackField('
            f'id: {self.id}, '
            f'type: {self.type}, '
            f'track_type: {self.track_type}, '
            f'name: {self.name}, '
            f'is_required: {self.is_required}, '
            f'user_id: {self.user_id})'
        )


def get_custom_fields_by_track_type() -> dict[TrackType, list[CustomTrackField]]:
    customFieldsByTrackType = {}
    for trackType in TrackType:
        customFieldsByTrackType[trackType] = (
            CustomTrackField.query.filter(CustomTrackField.user_id == current_user.id)
            .filter(CustomTrackField.track_type == trackType)
            .all()
        )
    return customFieldsByTrackType


RESERVED_FIELD_NAMES = [
    'name',
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
]
