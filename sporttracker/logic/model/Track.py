import enum
from dataclasses import dataclass
from datetime import datetime

from flask_babel import gettext
from flask_login import current_user
from sqlalchemy import Integer, String, DateTime, extract, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import mapped_column, Mapped, relationship

from sporttracker.logic.DateTimeAccess import DateTimeAccess
from sporttracker.logic.model.Participant import Participant, track_participant_association
from sporttracker.logic.model.User import User
from sporttracker.logic.model.db import db


class TrackType(enum.Enum):
    BIKING = 'BIKING', 'directions_bike', False, 'bg-warning', '#FFC107', 'border-warning', True, 0
    RUNNING = 'RUNNING', 'directions_run', False, 'bg-info', '#0DCAF0', 'border-info', False, 1
    HIKING = 'HIKING', 'hiking', False, 'bg-green', '#619B8A', 'border-green', True, 2

    icon: str
    is_font_awesome_icon: bool
    background_color: str
    background_color_hex: str
    border_color: str
    render_speed_in_kph: bool
    order: int

    def __new__(
        cls,
        name: str,
        icon: str,
        is_font_awesome_icon: bool,
        background_color: str,
        background_color_hex: str,
        border_color: str,
        render_speed_in_kph: bool,
        order: int,
    ):
        member = object.__new__(cls)
        member._value_ = name
        member.icon = icon
        member.is_font_awesome_icon = is_font_awesome_icon
        member.background_color = background_color
        member.background_color_hex = background_color_hex
        member.border_color = border_color
        member.render_speed_in_kph = render_speed_in_kph
        member.order = order
        return member

    def get_localized_name(self) -> str:
        # must be done this way to include translations in *.po and *.mo file
        if self == self.BIKING:
            return gettext('Biking')
        elif self == self.RUNNING:
            return gettext('Running')
        elif self == self.HIKING:
            return gettext('Hiking')

        raise ValueError(f'Could not get localized name for unsupported TrackType: {self}')


class Track(db.Model, DateTimeAccess):  # type: ignore[name-defined]
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type = db.Column(db.Enum(TrackType))
    name: Mapped[String] = mapped_column(String, nullable=False)
    startTime: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=True)
    distance: Mapped[int] = mapped_column(Integer, nullable=False)
    averageHeartRate: Mapped[int] = mapped_column(Integer, nullable=True)
    elevationSum: Mapped[int] = mapped_column(Integer, nullable=True)
    gpxFileName: Mapped[str] = mapped_column(String, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    custom_fields = db.Column(JSON)
    participants: Mapped[list[Participant]] = relationship(secondary=track_participant_association)

    def get_date_time(self) -> datetime:
        return self.startTime  # type: ignore[return-value]

    def __repr__(self):
        return (
            f'Track('
            f'id: {self.id}, '
            f'type: {self.type}, '
            f'name: {self.name}, '
            f'startTime: {self.startTime}, '
            f'duration: {self.duration}, '
            f'distance: {self.distance}, '
            f'averageHeartRate: {self.averageHeartRate}, '
            f'elevationSum: {self.elevationSum}, '
            f'gpxFileName: {self.gpxFileName}, '
            f'custom_fields: {self.custom_fields}, '
            f'participants: {self.participants}, '
            f'user_id: {self.user_id})'
        )


def get_track_names_by_track_type(trackType: TrackType) -> list[str]:
    rows = (
        Track.query.with_entities(Track.name)
        .filter(Track.user_id == current_user.id)
        .filter(Track.type == trackType)
        .distinct()
        .order_by(Track.name.asc())
        .all()
    )

    return [row[0] for row in rows]


def get_number_of_all_tracks() -> int:
    return Track.query.count()


def get_tracks_by_year_and_month_by_type(
    year: int, month: int, trackTypes: list[TrackType]
) -> list[Track]:
    return (
        Track.query.join(User)
        .filter(Track.type.in_(trackTypes))
        .filter(User.username == current_user.username)
        .filter(extract('year', Track.startTime) == year)
        .filter(extract('month', Track.startTime) == month)
        .order_by(Track.startTime.desc())
        .all()
    )


@dataclass
class MonthDistanceSum:
    year: int
    month: int
    distanceSum: float


def get_distance_per_month_by_type(
    trackType: TrackType, minYear: int, maxYear: int
) -> list[MonthDistanceSum]:
    year = extract('year', Track.startTime)
    month = extract('month', Track.startTime)

    rows = (
        Track.query.with_entities(
            func.sum(Track.distance / 1000).label('distanceSum'),
            year.label('year'),
            month.label('month'),
        )
        .filter(Track.type == trackType)
        .filter(Track.user_id == current_user.id)
        .group_by(year, month)
        .order_by(year, month)
        .all()
    )

    result = []
    for currentYear in range(minYear, maxYear + 1):
        for currentMonth in range(1, 13):
            for row in rows:
                if row.year == currentYear and row.month == currentMonth:
                    result.append(
                        MonthDistanceSum(
                            year=currentYear, month=currentMonth, distanceSum=float(row.distanceSum)
                        )
                    )
                    break
            else:
                result.append(
                    MonthDistanceSum(year=currentYear, month=currentMonth, distanceSum=0.0)
                )

    return result


def get_available_years() -> list[int]:
    year = extract('year', Track.startTime)

    rows = (
        Track.query.with_entities(year.label('year'))
        .filter(Track.user_id == current_user.id)
        .group_by(year)
        .order_by(year)
        .all()
    )

    if rows is None:
        return []

    return [int(row.year) for row in rows]


def get_distance_since_date(date: datetime | DateTime, trackTypes: list[TrackType]) -> int:
    return int(
        Track.query.with_entities(func.sum(Track.distance))
        .filter(Track.type.in_(trackTypes))
        .filter(Track.user_id == current_user.id)
        .filter(Track.startTime > date)
        .scalar()
        or 0
    )


def get_track_by_id(track_id: int) -> Track | None:
    return Track.query.filter(Track.user_id == current_user.id).filter(Track.id == track_id).first()
