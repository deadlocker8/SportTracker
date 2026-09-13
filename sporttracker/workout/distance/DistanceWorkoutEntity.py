from dataclasses import dataclass
from typing import ClassVar

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sporttracker.db import db
from sporttracker.gpx.GpxMetadataEntity import GpxMetadata
from sporttracker.plannedTour.PlannedTourEntity import (
    PlannedTour,
    distance_workout_planned_tour_association,
)
from sporttracker.workout.WorkoutEntity import Workout


class DistanceWorkout(Workout):  # type: ignore[name-defined]
    __tablename__ = 'distance_workout'
    id: Mapped[int] = mapped_column(ForeignKey('workout.id', ondelete='CASCADE'), primary_key=True)
    distance: Mapped[int] = mapped_column(Integer, nullable=False)
    elevation_sum: Mapped[int] = mapped_column(Integer, nullable=True)
    share_code: Mapped[str] = mapped_column(String, nullable=True)
    gpx_metadata_id = db.Column(db.Integer, db.ForeignKey('gpx_metadata.id', ondelete='SET NULL'), nullable=True)
    planned_tour: Mapped[PlannedTour] = relationship(secondary=distance_workout_planned_tour_association)

    __mapper_args__: ClassVar[dict[str, str]] = {
        'polymorphic_identity': 'distance_workout',
    }

    def __repr__(self):
        return (
            f'DistanceWorkout('
            f'id: {self.id}, '
            f'name: {self.name}, '
            f'start_time: {self.start_time}, '
            f'duration: {self.duration}, '
            f'custom_fields: {self.custom_fields}, '
            f'participants: {self.participants}, '
            f'user_id: {self.user_id}, '
            f'average_heart_rate: {self.average_heart_rate}, '
            f'distance: {self.distance}, '
            f'elevation_sum: {self.elevation_sum}, '
            f'share_code: {self.share_code},'
            f'gpx_metadata_id: {self.gpx_metadata_id})'
        )

    def get_gpx_metadata(self) -> GpxMetadata | None:
        if self.gpx_metadata_id is None:
            return None
        else:
            return db.session.get(GpxMetadata, self.gpx_metadata_id)

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
