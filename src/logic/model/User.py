import enum

from flask_babel import gettext
from flask_bcrypt import Bcrypt
from flask_login import UserMixin
from sqlalchemy import Integer, String, Boolean
from sqlalchemy.orm import mapped_column, Mapped

from logic.model.db import db


class Language(enum.Enum):
    ENGLISH = 'ENGLISH', 'en', 'English'
    GERMAN = 'GERMAN', 'de', 'Deutsch'

    def __new__(cls, name: str, shortCode: str, localizedName: str):
        member = object.__new__(cls)
        member._value_ = name
        member.shortCode = shortCode  # type: ignore[attr-defined]
        member.localizedName = localizedName  # type: ignore[attr-defined]
        return member


class User(UserMixin, db.Model):  # type: ignore[name-defined]
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    isAdmin: Mapped[bool] = mapped_column(Boolean, nullable=False)
    language = db.Column(db.Enum(Language))
    tracks = db.relationship('Track', backref='user', lazy=True, cascade='delete')
    customFields = db.relationship('CustomTrackField', backref='user', lazy=True, cascade='delete')
    trackInfoItems = db.relationship('TrackInfoItem', backref='user', lazy=True, cascade='delete')


class TrackInfoItemType(enum.Enum):
    DISTANCE = 'DISTANCE'
    DURATION = 'DURATION'
    SPEED = 'SPEED'
    AVERAGE_HEART_RATE = 'AVERAGE_HEART_RATE'
    ELEVATION_SUM = 'ELEVATION_SUM'

    def get_localized_name(self) -> str:
        if self == self.DISTANCE:
            return gettext('Distance')
        elif self == self.DURATION:
            return gettext('Duration')
        elif self == self.SPEED:
            return gettext('Average Speed')
        elif self == self.AVERAGE_HEART_RATE:
            return gettext('Average Heart Rate')
        elif self == self.ELEVATION_SUM:
            return gettext('Elevation Sum')

        raise ValueError(f'Could not get localized name for unsupported TrackInfoItemType: {self}')


class TrackInfoItem(db.Model):  # type: ignore[name-defined]
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type = db.Column(db.Enum(TrackInfoItemType))
    is_activated: Mapped[bool] = mapped_column(Boolean, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


def create_user(username: str, password: str, isAdmin: bool, language: Language) -> User:
    user = User(
        username=username,
        password=Bcrypt().generate_password_hash(password).decode('utf-8'),
        isAdmin=isAdmin,
        language=language,
    )
    db.session.add(user)
    db.session.commit()

    for itemType in TrackInfoItemType:
        trackInfoItem = TrackInfoItem(type=itemType, is_activated=True, user_id=user.id)
        db.session.add(trackInfoItem)
    db.session.commit()

    return user
