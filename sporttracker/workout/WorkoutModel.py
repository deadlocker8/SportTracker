from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, field_validator

from sporttracker.gpx.GpxMetadataEntity import GpxMetadata
from sporttracker.helpers.DateTimeAccess import DateTimeAccess
from sporttracker.maintenance.MaintenanceEventInstanceEntity import (
    MaintenanceEvent,
)
from sporttracker.monthGoal.MonthGoalEntity import (
    MonthGoalSummary,
)
from sporttracker.user.UserEntity import get_user_by_id
from sporttracker.workout.HeartRateEntity import HeartRateEntity
from sporttracker.workout.distance.DistanceWorkoutEntity import (
    DistanceWorkout,
)
from sporttracker.workout.fitness.FitnessWorkoutCategory import FitnessWorkoutCategoryType
from sporttracker.workout.fitness.FitnessWorkoutEntity import FitnessWorkout
from sporttracker.workout.fitness.FitnessWorkoutType import FitnessWorkoutType


@dataclass
class BaseWorkoutModel(DateTimeAccess):
    id: int
    name: str
    type: str
    start_time: datetime
    duration: int
    participants: list[str]
    ownerName: str
    average_heart_rate: int | None

    def get_date_time(self) -> datetime:
        return self.start_time

    def has_heart_rate_data(self) -> bool:
        return HeartRateEntity.query.filter(HeartRateEntity.workout_id == self.id).count()


@dataclass
class DistanceWorkoutModel(BaseWorkoutModel):
    distance: int
    elevation_sum: int | None
    gpx_metadata: GpxMetadata | None
    share_code: str | None

    @staticmethod
    def create_from_workout(
        workout: DistanceWorkout,
    ) -> 'DistanceWorkoutModel':
        return DistanceWorkoutModel(
            id=workout.id,
            name=workout.name,  # type: ignore[arg-type]
            type=workout.type,
            start_time=workout.start_time,  # type: ignore[arg-type]
            distance=workout.distance,
            duration=workout.duration,
            average_heart_rate=workout.average_heart_rate,
            elevation_sum=workout.elevation_sum,
            gpx_metadata=workout.get_gpx_metadata(),
            participants=[str(item.id) for item in workout.participants],
            share_code=workout.share_code,
            ownerName=get_user_by_id(workout.user_id).username,
        )


@dataclass
class FitnessWorkoutModel(BaseWorkoutModel):
    fitness_workout_categories: list[FitnessWorkoutCategoryType]
    fitness_workout_type: FitnessWorkoutType | None = None

    @staticmethod
    def create_from_workout(
        workout: FitnessWorkout,
    ) -> 'FitnessWorkoutModel':
        return FitnessWorkoutModel(
            id=workout.id,
            name=workout.name,  # type: ignore[arg-type]
            type=workout.type,
            start_time=workout.start_time,  # type: ignore[arg-type]
            duration=workout.duration,
            average_heart_rate=workout.average_heart_rate,
            participants=[str(item.id) for item in workout.participants],
            ownerName=get_user_by_id(workout.user_id).username,
            fitness_workout_categories=workout.get_workout_categories(),
            fitness_workout_type=workout.fitness_workout_type,
        )


@dataclass
class MonthModel:
    name: str
    entries: list[DistanceWorkoutModel | FitnessWorkoutModel | MaintenanceEvent]
    goals: list[MonthGoalSummary]


class BaseWorkoutFormModel(BaseModel):
    name: str
    type: str
    date: str
    time: str
    duration_hours: int
    duration_minutes: int
    duration_seconds: int
    participants: list[str] | str | None = None
    average_heart_rate: int | None = None

    def calculate_start_time(self) -> datetime:
        return datetime.strptime(f'{self.date} {self.time}', '%Y-%m-%d %H:%M')

    def calculate_duration(self) -> int:
        return 3600 * self.duration_hours + 60 * self.duration_minutes + self.duration_seconds

    @field_validator(*['average_heart_rate'], mode='before')
    def averageHeartRateCheck(cls, value: str, info) -> str | None:
        if isinstance(value, str):
            value = value.strip()
        if value == '':
            return None
        return value
