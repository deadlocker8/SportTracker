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
    BIKING = 'BIKING', 'Biking', 'directions_bike', False, 'bg-warning', '#FFC107', 'border-warning'
    RUNNING = 'RUNNING', 'Running', 'directions_run', False, 'bg-info', '#0DCAF0', 'border-info'
    HIKING = 'HIKING', 'Hiking', 'fa-person-hiking', True, 'bg-green', '#619B8A', 'border-green'

    localization_key: str
    icon: str
    is_font_awesome_icon: bool
    background_color: str
    background_color_hex: str
    border_color: str

    def __new__(
        cls,
        name: str,
        localization_key: str,
        icon: str,
        is_font_awesome_icon: bool,
        background_color: str,
        background_color_hex: str,
        border_color: str,
    ):
        member = object.__new__(cls)
        member._value_ = name
        member.localization_key = localization_key
        member.icon = icon
        member.is_font_awesome_icon = is_font_awesome_icon
        member.background_color = background_color
        member.background_color_hex = background_color_hex
        member.border_color = border_color
        return member

    def get_localized_name(self) -> str:
        return gettext(self.localization_key)


class Track(db.Model):  # type: ignore[name-defined]
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
