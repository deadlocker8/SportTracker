import enum
from dataclasses import dataclass

from flask_babel import gettext
from flask_login import current_user
from sqlalchemy import Integer, String, DateTime, extract, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import mapped_column, Mapped

from logic.model.User import User
from logic.model.db import db


class TrackType(enum.Enum):
    BIKING = 'BIKING', 'directions_bike', 'bg-warning', '#FFC107', 'border-warning'
    RUNNING = 'RUNNING', 'directions_run', 'bg-info', '#0DCAF0', 'border-info'

    def __new__(cls, name: str, icon: str, background_color: str, background_color_hex: str, border_color: str):
        member = object.__new__(cls)
        member._value_ = name
        member.icon = icon
        member.background_color = background_color
        member.background_color_hex = background_color_hex
        member.border_color = border_color
        return member

    def get_localized_name(self) -> str:
        if self == self.BIKING:
            return gettext('Biking')
        elif self == self.RUNNING:
            return gettext('Running')

        raise ValueError(f'Could not get localized name for unsupported TrackType: {self}')


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
    custom_fields = db.Column(JSON)


def get_track_names_by_track_type(trackType: TrackType) -> list[str]:
    rows = (Track.query.with_entities(Track.name)
            .filter(Track.user_id == current_user.id)
            .filter(Track.type == trackType)
            .distinct()
            .order_by(Track.name.asc())
            .all())

    return [row[0] for row in rows]


def get_number_of_all_tracks() -> int:
    return Track.query.count()


def get_tracks_by_year_and_month_by_type(year: int, month: int, trackTypes: list[TrackType]) -> list[Track]:
    return (Track.query.join(User)
            .filter(Track.type.in_(trackTypes))
            .filter(User.username == current_user.username)
            .filter(extract('year', Track.startTime) == year)
            .filter(extract('month', Track.startTime) == month)
            .order_by(Track.startTime.desc())
            .all())


@dataclass
class MonthDistanceSum:
    year: int
    month: int
    distanceSum: float


def get_distance_per_month_by_type(trackType: TrackType, minYear: int, maxYear: int) -> list[MonthDistanceSum]:
    year = extract('year', Track.startTime)
    month = extract('month', Track.startTime)

    rows = (Track.query
            .with_entities(func.sum(Track.distance / 1000).label('distanceSum'),
                           year.label('year'),
                           month.label('month'))
            .filter(Track.type == trackType)
            .filter(Track.user_id == current_user.id)
            .group_by(year, month)
            .order_by(year, month)
            .all())

    result = []
    for year in range(minYear, maxYear + 1):
        for month in range(1, 13):
            for row in rows:
                if row.year == year and row.month == month:
                    result.append(MonthDistanceSum(year=year, month=month, distanceSum=float(row.distanceSum)))
                    break
            else:
                result.append(MonthDistanceSum(year=year, month=month, distanceSum=0.0))

    return result
