from dataclasses import dataclass
from datetime import datetime

from flask_login import current_user
from sqlalchemy import Integer, String, DateTime, extract, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import mapped_column, Mapped, relationship

from sporttracker.logic.model.GpxMetadata import GpxMetadata
from sporttracker.logic.model.Participant import Participant, track_participant_association
from sporttracker.logic.model.PlannedTour import PlannedTour, track_planned_tour_association
from sporttracker.logic.model.TrackType import TrackType
from sporttracker.logic.model.User import User
from sporttracker.logic.model.WorkoutCategory import WorkoutCategory
from sporttracker.logic.model.WorkoutType import WorkoutType
from sporttracker.logic.model.db import db


class Track(db.Model):  # type: ignore[name-defined]
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
    participants: Mapped[list[Participant]] = relationship(secondary=track_participant_association)
    share_code: Mapped[str] = mapped_column(String, nullable=True)
    plannedTour: Mapped[PlannedTour] = relationship(secondary=track_planned_tour_association)
    gpx_metadata_id = db.Column(db.Integer, db.ForeignKey('gpx_metadata.id'), nullable=True)
    workout_type = db.Column(db.Enum(WorkoutType), nullable=True)

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
            f'custom_fields: {self.custom_fields}, '
            f'participants: {self.participants}, '
            f'user_id: {self.user_id}, '
            f'share_code: {self.share_code},'
            f'gpx_metadata_id: {self.gpx_metadata_id})'
        )

    def get_gpx_metadata(self) -> GpxMetadata | None:
        if self.gpx_metadata_id is None:
            return None
        else:
            return GpxMetadata.query.get(self.gpx_metadata_id)

    def get_download_name(self) -> str:
        escapedName = ''.join([c if c.isalnum() else '_' for c in str(self.name)])
        return f'{self.id} - {escapedName}'

    def clear_attributes_for_track_type(self) -> None:
        trackType = TrackType(self.type)  # type: ignore[call-arg]
        if trackType.supports_distance:
            self.workout_type = None
        else:
            self.distance = 0
            self.elevationSum = None  # type: ignore[assignment]
            self.gpx_metadata_id = None
            self.plannedTour = None  # type: ignore[assignment]
            self.share_code = None  # type: ignore[assignment]

    def get_workout_categories(self) -> list[str]:
        return [
            c.workout_category_type
            for c in WorkoutCategory.query.filter(WorkoutCategory.track_id == self.id).all()
        ]


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


@dataclass
class MonthDurationSum:
    year: int
    month: int
    durationSum: int


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


def get_duration_per_month_by_type(
    trackType: TrackType, minYear: int, maxYear: int
) -> list[MonthDurationSum]:
    year = extract('year', Track.startTime)
    month = extract('month', Track.startTime)

    rows = (
        Track.query.with_entities(
            func.sum(Track.duration).label('durationSum'),
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
                        MonthDurationSum(
                            year=currentYear, month=currentMonth, durationSum=int(row.durationSum)
                        )
                    )
                    break
            else:
                result.append(MonthDurationSum(year=currentYear, month=currentMonth, durationSum=0))

    return result


def get_available_years(userId) -> list[int]:
    year = extract('year', Track.startTime)

    rows = (
        Track.query.with_entities(year.label('year'))
        .filter(Track.user_id == userId)
        .group_by(year)
        .order_by(year)
        .all()
    )

    if rows is None:
        return []

    return [int(row.year) for row in rows]


def get_distance_between_dates(
    startDateTime: datetime | DateTime,
    endDateTime: datetime | DateTime,
    trackTypes: list[TrackType],
) -> int:
    return int(
        Track.query.with_entities(func.sum(Track.distance))
        .filter(Track.type.in_(trackTypes))
        .filter(Track.user_id == current_user.id)
        .filter(Track.startTime.between(startDateTime, endDateTime))
        .scalar()
        or 0
    )


def get_track_by_id(track_id: int) -> Track | None:
    return Track.query.filter(Track.user_id == current_user.id).filter(Track.id == track_id).first()


def get_track_by_share_code(shareCode: str) -> Track | None:
    return Track.query.filter(Track.share_code == shareCode).first()


def get_track_ids_by_planned_tour(plannedTour: PlannedTour) -> list[int]:
    linkedTrackIds = (
        Track.query.with_entities(Track.id)
        .filter(Track.user_id == current_user.id)
        .filter(Track.plannedTour == plannedTour)
        .all()
    )

    if linkedTrackIds is None:
        return []

    return [int(row.id) for row in linkedTrackIds]
