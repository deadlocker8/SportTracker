import enum

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
        member.shortCode = shortCode
        member.localizedName = localizedName
        return member


class User(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    isAdmin: Mapped[bool] = mapped_column(Boolean, nullable=False)
    language = db.Column(db.Enum(Language))
    tracks = db.relationship('Track', backref='user', lazy=True, cascade='delete')
    customFields = db.relationship('CustomTrackField', backref='user', lazy=True, cascade='delete')
