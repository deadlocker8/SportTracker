import enum

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, DateTime, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

db = SQLAlchemy()


class User(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    isAdmin: Mapped[bool] = mapped_column(Boolean, nullable=False)
    tracks = db.relationship('Track', backref='user', lazy=True, cascade='delete')


class TrackType(enum.Enum):
    BICYCLE = 'BICYCLE', 'directions_bike', 'bg-warning', '#FFC107'
    RUNNING = 'RUNNING', 'directions_run', 'bg-info', '#0DCAF0'

    def __new__(cls, name: str, icon: str, background_color: str, background_color_hex: str):
        member = object.__new__(cls)
        member._value_ = name
        member.icon = icon
        member.background_color = background_color
        member.background_color_hex = background_color_hex
        return member


class Track(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type = db.Column(db.Enum(TrackType))
    name: Mapped[String] = mapped_column(String, nullable=False)
    startTime: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=True)
    distance: Mapped[int] = mapped_column(Integer, nullable=False)
    averageHeartRate: Mapped[int] = mapped_column(Integer, nullable=True)
    elevationSum: Mapped[int] = mapped_column(Integer, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class MonthGoal(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type = db.Column(db.Enum(TrackType))
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    distance_minimum: Mapped[int] = mapped_column(Integer, nullable=False)
    distance_perfect: Mapped[int] = mapped_column(Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
