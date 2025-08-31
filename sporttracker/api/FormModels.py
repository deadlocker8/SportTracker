from datetime import datetime

from pydantic import BaseModel


class MonthGoalDistanceApiFormModel(BaseModel):
    workout_type: str
    year: int
    month: int
    distance_minimum: float
    distance_perfect: float


class MonthGoalCountApiFormModel(BaseModel):
    workout_type: str
    year: int
    month: int
    count_minimum: float
    count_perfect: float


class MonthGoalDurationApiFormModel(BaseModel):
    workout_type: str
    year: int
    month: int
    duration_minimum: float
    duration_perfect: float


class DistanceWorkoutApiFormModel(BaseModel):
    name: str
    workout_type: str
    date: str
    start_time: str
    distance: int
    duration: int
    participants: list[int]
    average_heart_rate: int | None = None
    elevation_sum: int | None = None
    planned_tour_id: int | None = None
    custom_fields: dict[str, str | int | float] | None = None

    def calculate_start_time(self) -> datetime:
        return datetime.strptime(f'{self.date} {self.start_time}', '%Y-%m-%d %H:%M')


class FitnessWorkoutApiFormModel(BaseModel):
    name: str
    workout_type: str
    date: str
    start_time: str
    duration: int
    participants: list[int]
    fitness_workout_type: str
    fitness_workout_categories: list[str] | None = None
    average_heart_rate: int | None = None
    custom_fields: dict[str, str | int | float] | None = None

    def calculate_start_time(self) -> datetime:
        return datetime.strptime(f'{self.date} {self.start_time}', '%Y-%m-%d %H:%M')


class HeartRateDataModel(BaseModel):
    timestamp: str
    bpm: int


class HeartRateDataListModel(BaseModel):
    data: list[HeartRateDataModel]
