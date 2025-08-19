from dataclasses import dataclass
from datetime import datetime

from flask_login import current_user
from sqlalchemy import Integer, String, DateTime, extract, func, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from sporttracker.gpx.GpxMetadataEntity import GpxMetadata
from sporttracker.plannedTour.PlannedTourEntity import (
    PlannedTour,
    distance_workout_planned_tour_association,
)
from sporttracker.workout.WorkoutEntity import Workout
from sporttracker.workout.WorkoutType import WorkoutType
from sporttracker.db import db


class DistanceWorkout(Workout):  # type: ignore[name-defined]
    __tablename__ = 'distance_workout'
    id: Mapped[int] = mapped_column(ForeignKey('workout.id'), primary_key=True)
    distance: Mapped[int] = mapped_column(Integer, nullable=False)
    elevation_sum: Mapped[int] = mapped_column(Integer, nullable=True)
    share_code: Mapped[str] = mapped_column(String, nullable=True)
    gpx_metadata_id = db.Column(db.Integer, db.ForeignKey('gpx_metadata.id'), nullable=True)
    planned_tour: Mapped[PlannedTour] = relationship(secondary=distance_workout_planned_tour_association)

    __mapper_args__ = {
        'polymorphic_identity': 'distance_workout',
    }

    def __repr__(self):
        return (
            f'DistanceWorkout('
            f'name: {self.name}, '
            f'start_time: {self.start_time}, '
            f'duration: {self.duration}, '
            f'custom_fields: {self.custom_fields}, '
            f'participants: {self.participants}, '
            f'user_id: {self.user_id}, '
            f'average_heart_rate: {self.average_heart_rate}, '
            f'distance: {self.distance}, '
            f'elevation_sum: {self.elevation_sum}, '
            f'custom_fields: {self.custom_fields}, '
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


def get_number_of_all_distance_workouts() -> int:
    return DistanceWorkout.query.count()


@dataclass
class MonthDistanceSum:
    year: int
    month: int
    distanceSum: float


def get_distance_per_month_by_type(workoutType: WorkoutType, minYear: int, maxYear: int) -> list[MonthDistanceSum]:
    year = extract('year', DistanceWorkout.start_time)
    month = extract('month', DistanceWorkout.start_time)

    rows = (
        DistanceWorkout.query.with_entities(
            func.sum(DistanceWorkout.distance / 1000).label('distanceSum'),
            year.label('year'),
            month.label('month'),
        )
        .filter(DistanceWorkout.type == workoutType)
        .filter(DistanceWorkout.user_id == current_user.id)
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
                        MonthDistanceSum(year=currentYear, month=currentMonth, distanceSum=float(row.distanceSum))
                    )
                    break
            else:
                result.append(MonthDistanceSum(year=currentYear, month=currentMonth, distanceSum=0.0))

    return result


def get_available_years(userId) -> list[int]:
    year = extract('year', DistanceWorkout.start_time)

    rows = (
        DistanceWorkout.query.with_entities(year.label('year'))
        .filter(DistanceWorkout.user_id == userId)
        .group_by(year)
        .order_by(year)
        .all()
    )

    if rows is None:
        return []

    return [int(row.year) for row in rows]


def get_distance_between_dates(
    userId: int,
    startDateTime: datetime | DateTime,
    endDateTime: datetime | DateTime,
    workoutTypes: list[WorkoutType],
    customWorkoutFieldName: str | None = None,
    customWorkoutFieldValue: str | None = None,
) -> int:
    query = (
        DistanceWorkout.query.with_entities(func.sum(DistanceWorkout.distance))
        .filter(DistanceWorkout.type.in_(workoutTypes))
        .filter(DistanceWorkout.user_id == userId)
        .filter(DistanceWorkout.start_time.between(startDateTime, endDateTime))
    )

    if customWorkoutFieldName is not None and customWorkoutFieldValue is not None:
        query = query.filter(
            DistanceWorkout.custom_fields[customWorkoutFieldName].astext.cast(String) == customWorkoutFieldValue
        )

    return int(query.scalar() or 0)


def get_distance_workout_ids_by_planned_tour(plannedTour: PlannedTour) -> list[int]:
    linkedIds = (
        DistanceWorkout.query.with_entities(DistanceWorkout.id)
        .filter(DistanceWorkout.user_id == current_user.id)
        .filter(DistanceWorkout.planned_tour == plannedTour)
        .all()
    )

    if linkedIds is None:
        return []

    return [int(row.id) for row in linkedIds]
