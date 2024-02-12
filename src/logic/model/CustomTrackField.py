import enum

from flask_babel import gettext
from flask_login import current_user
from sqlalchemy import Integer, String, Boolean
from sqlalchemy.orm import mapped_column, Mapped

from logic.model.Track import TrackType
from logic.model.db import db


class CustomTrackFieldType(enum.Enum):
    STRING = 'STRING', 'String'
    INTEGER = 'INTEGER', 'Integer'
    FLOAT = 'FLOAT', 'Float'

    def __new__(cls, name: str, localization_key: str):
        member = object.__new__(cls)
        member._value_ = name
        member.localization_key = localization_key  # type: ignore[attr-defined]
        return member

    def get_localized_name(self) -> str:
        return gettext(self.localization_key)  # type: ignore[attr-defined]


class CustomTrackField(db.Model):  # type: ignore[name-defined]
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type = db.Column(db.Enum(CustomTrackFieldType))
    track_type = db.Column(db.Enum(TrackType))
    name: Mapped[String] = mapped_column(String, nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


def get_custom_fields_by_track_type() -> dict[TrackType, list[CustomTrackField]]:
    customFieldsByTrackType = {}
    for trackType in TrackType:
        customFieldsByTrackType[trackType] = (
            CustomTrackField.query.filter(CustomTrackField.user_id == current_user.id)
            .filter(CustomTrackField.track_type == trackType)
            .all()
        )
    return customFieldsByTrackType
