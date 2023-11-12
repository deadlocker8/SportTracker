import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import ClassVar

from flask_login import UserMixin, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, DateTime, String, Boolean, extract
from sqlalchemy.orm import Mapped, mapped_column

db = SQLAlchemy()


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
    bikingTracks = db.relationship('BikingTrack', backref='user', lazy=True, cascade='delete')
    runningTracks = db.relationship('RunningTrack', backref='user', lazy=True, cascade='delete')


class TrackType(enum.Enum):
    BIKING = 'BIKING', 'directions_bike', 'bg-warning', '#FFC107'
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
    type = TrackType.BIKING
    bike: Mapped[String] = mapped_column(String, nullable=True)


class RunningTrack(Track):
    type = TrackType.RUNNING


@dataclass
class MonthGoalSummary(ABC):
    id: int
    type: TrackType
    name: str
    percentage: float
    color: str

    @abstractmethod
    def get_actual_value_formatted(self) -> str:
        pass


@dataclass
class MonthGoalDistanceSummary(MonthGoalSummary):
    type_name: ClassVar[str] = 'DISTANCE'
    icon: ClassVar[str] = 'route'

    goal_distance_minimum: float
    goal_distance_perfect: float
    actual_distance: float

    def get_actual_value_formatted(self) -> str:
        value = str(int(self.actual_distance))

        if len(value) == 1:
            return f'&nbsp;&nbsp;{value} km'
        elif len(value) == 2:
            return f'&nbsp;{value} km'
        else:
            return f'{value} km'


@dataclass
class MonthGoalCountSummary(MonthGoalSummary):
    type_name: ClassVar[str] = 'COUNT'
    icon: ClassVar[str] = 'format_list_numbered'

    goal_count_minimum: float
    goal_count_perfect: float
    actual_count: float

    def get_actual_value_formatted(self) -> str:
        return f'{self.actual_count} / {self.goal_count_perfect}'


class MonthGoal(db.Model):
    __abstract__ = True
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type = db.Column(db.Enum(TrackType))
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    @abstractmethod
    def get_summary(self) -> MonthGoalSummary:
        pass


class MonthGoalDistance(MonthGoal):
    distance_minimum: Mapped[int] = mapped_column(Integer, nullable=False)
    distance_perfect: Mapped[int] = mapped_column(Integer, nullable=False)

    def get_summary(self) -> MonthGoalDistanceSummary:
        tracks = get_tracks_by_year_and_month_by_type(self.year, self.month, get_track_class_by_ty_type(self.type))

        actualDistance = 0
        if tracks:
            actualDistance = sum([t.distance for t in tracks])

        color = self.__determine_color(actualDistance)
        name = date(year=self.year, month=self.month, day=1).strftime('%B %y')
        percentage = actualDistance / self.distance_perfect * 100
        return MonthGoalDistanceSummary(id=self.id,
                                        type=self.type,
                                        name=name,
                                        goal_distance_minimum=self.distance_minimum / 1000,
                                        goal_distance_perfect=self.distance_perfect / 1000,
                                        actual_distance=actualDistance / 1000,
                                        percentage=percentage,
                                        color=color)

    def __determine_color(self, actualDistance: float) -> str:
        if actualDistance >= self.distance_perfect:
            return 'bg-success'
        elif actualDistance >= self.distance_minimum:
            return 'bg-warning'

        return 'bg-danger'


class MonthGoalCount(MonthGoal):
    count_minimum: Mapped[int] = mapped_column(Integer, nullable=False)
    count_perfect: Mapped[int] = mapped_column(Integer, nullable=False)

    def get_summary(self) -> MonthGoalCountSummary:
        tracks = get_tracks_by_year_and_month_by_type(self.year, self.month, get_track_class_by_ty_type(self.type))

        actualCount = 0
        if tracks:
            actualCount = len(tracks)

        color = self.__determine_color(actualCount)
        name = date(year=self.year, month=self.month, day=1).strftime('%B %y')
        percentage = actualCount / self.count_perfect * 100
        return MonthGoalCountSummary(id=self.id,
                                     type=self.type,
                                     name=name,
                                     goal_count_minimum=self.count_minimum,
                                     goal_count_perfect=self.count_perfect,
                                     actual_count=actualCount,
                                     percentage=percentage,
                                     color=color)

    def __determine_color(self, actualCount: float) -> str:
        if actualCount >= self.count_perfect:
            return 'bg-success'
        elif actualCount >= self.count_minimum:
            return 'bg-warning'

        return 'bg-danger'


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
            .order_by(trackClass.startTime.desc())
            .all())


def get_track_class_by_ty_type(trackType: TrackType):
    if trackType == TrackType.BIKING:
        return BikingTrack

    if trackType == TrackType.RUNNING:
        return RunningTrack

    raise ValueError(f'Could not determine track class for track type "{trackType}"')


def get_goal_summaries_by_year_and_month(year: int, month: int) -> list[MonthGoalSummary]:
    goalsDistance = (MonthGoalDistance.query.join(User)
                     .filter(User.username == current_user.username)
                     .filter(MonthGoalDistance.year == year)
                     .filter(MonthGoalDistance.month == month)
                     .all())
    goalsCount = (MonthGoalCount.query.join(User)
                  .filter(User.username == current_user.username)
                  .filter(MonthGoalCount.year == year)
                  .filter(MonthGoalCount.month == month)
                  .all())

    return [goal.get_summary() for goal in goalsDistance + goalsCount]
