import enum

from flask_login import UserMixin, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, DateTime, String, Boolean, extract
from sqlalchemy.orm import Mapped, mapped_column

db = SQLAlchemy()


class User(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    isAdmin: Mapped[bool] = mapped_column(Boolean, nullable=False)
    bikingTracks = db.relationship('BikingTrack', backref='user', lazy=True, cascade='delete')
    runningTracks = db.relationship('RunningTrack', backref='user', lazy=True, cascade='delete')


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
    __abstract__ = True
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[String] = mapped_column(String, nullable=False)
    startTime: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=True)
    distance: Mapped[int] = mapped_column(Integer, nullable=False)
    averageHeartRate: Mapped[int] = mapped_column(Integer, nullable=True)
    elevationSum: Mapped[int] = mapped_column(Integer, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class BikingTrack(Track):
    type = TrackType.BICYCLE
    bike: Mapped[String] = mapped_column(String, nullable=True)


class RunningTrack(Track):
    type = TrackType.RUNNING


class MonthGoal(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type = db.Column(db.Enum(TrackType))
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    distance_minimum: Mapped[int] = mapped_column(Integer, nullable=False)
    distance_perfect: Mapped[int] = mapped_column(Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


def get_number_of_all_tracks() -> int:
    return BikingTrack.query.count() + RunningTrack.query.count()


def get_tracks_by_year_and_month(year: int, month: int) -> list[Track]:
    bikingTracks = get_tracks_by_year_and_month_by_type(year, month, BikingTrack)
    runningTracks = get_tracks_by_year_and_month_by_type(year, month, RunningTrack)

    return sorted(bikingTracks + runningTracks, key=lambda track: track.startTime)


def get_tracks_by_year_and_month_by_type(year: int, month: int, trackClass) -> list[Track]:
    return (trackClass.query.join(User)
            .filter(User.username == current_user.username)
            .filter(extract('year', trackClass.startTime) == year)
            .filter(extract('month', trackClass.startTime) == month)
            .order_by(trackClass.startTime.desc()).all())


def get_track_class_by_ty_type(trackType: TrackType):
    if trackType == TrackType.BICYCLE:
        return BikingTrack

    if trackType == TrackType.RUNNING:
        return RunningTrack

    raise ValueError(f'Could not determine track class for track type "{trackType}"')
