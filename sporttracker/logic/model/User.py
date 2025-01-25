import enum
from datetime import datetime

from flask_babel import gettext
from flask_bcrypt import Bcrypt
from flask_login import UserMixin, current_user
from sqlalchemy import Integer, String, Boolean, DateTime
from sqlalchemy.orm import mapped_column, Mapped

from sporttracker.logic.model.db import db


class Language(enum.Enum):
    ENGLISH = 'ENGLISH', 'en', 'English'
    GERMAN = 'GERMAN', 'de', 'Deutsch'

    shortCode: str
    localized_name: str

    def __new__(cls, name: str, shortCode: str, localized_name: str):
        member = object.__new__(cls)
        member._value_ = name
        member.shortCode = shortCode
        member.localized_name = localized_name
        return member


class User(UserMixin, db.Model):  # type: ignore[name-defined]
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    isAdmin: Mapped[bool] = mapped_column(Boolean, nullable=False)
    language = db.Column(db.Enum(Language))
    sports = db.relationship('Sport', backref='user', lazy=True, cascade='delete')
    customFields = db.relationship('CustomSportField', backref='user', lazy=True, cascade='delete')
    distance_sport_info_items = db.relationship(
        'DistanceSportInfoItem', backref='user', lazy=True, cascade='delete'
    )
    planned_tours_last_viewed_date: Mapped[DateTime] = mapped_column(DateTime)
    isTileHuntingActivated: Mapped[bool] = mapped_column(Boolean, nullable=False)
    isTileHuntingAccessActivated: Mapped[bool] = mapped_column(Boolean, nullable=False)
    tileHuntingShareCode: Mapped[str] = mapped_column(String, nullable=True)

    def __repr__(self):
        return (
            f'User('
            f'id: {self.id}, '
            f'username: {self.username}, '
            f'isAdmin: {self.isAdmin}, '
            f'language: {self.language}, '
            f'planned_tours_last_viewed_date: {self.planned_tours_last_viewed_date})'
            f'isTileHuntingActivated: {self.isTileHuntingActivated})'
            f'isTileHuntingAccessActivated: {self.isTileHuntingAccessActivated})'
            f'tileHuntingShareCode: {self.tileHuntingShareCode})'
        )


class DistanceSportInfoItemType(enum.Enum):
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

        raise ValueError(
            f'Could not get localized name for unsupported DistanceSportInfoItemType: {self}'
        )


class DistanceSportInfoItem(db.Model):  # type: ignore[name-defined]
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type = db.Column(db.Enum(DistanceSportInfoItemType))
    is_activated: Mapped[bool] = mapped_column(Boolean, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


def create_user(username: str, password: str, isAdmin: bool, language: Language) -> User:
    user = User(
        username=username,
        password=Bcrypt().generate_password_hash(password).decode('utf-8'),
        isAdmin=isAdmin,
        language=language,
        planned_tours_last_viewed_date=datetime.now(),
        isTileHuntingActivated=True,
        isTileHuntingAccessActivated=False,
        tileHuntingShareCode=None,
    )
    db.session.add(user)
    db.session.commit()

    for itemType in DistanceSportInfoItemType:
        distanceSportInfoItem = DistanceSportInfoItem(
            type=itemType, is_activated=True, user_id=user.id
        )
        db.session.add(distanceSportInfoItem)
    db.session.commit()

    return user


def get_user_by_id(identifier: int) -> User:
    return User.query.filter(User.id == identifier).first()


def get_users_by_ids(ids: list[int]) -> list[User]:
    return User.query.filter(User.id.in_(ids)).all()


def get_all_users_except_self_and_admin() -> list[User]:
    return User.query.filter(User.id != current_user.id).filter(User.isAdmin.is_(False)).all()


def get_user_by_tile_hunting_shared_code(share_code: str) -> User | None:
    return User.query.filter(User.tileHuntingShareCode == share_code).first()
