from dataclasses import dataclass


@dataclass
class MonthGoalDistanceApiModel:
    id: int
    workout_type: str
    year: int
    month: int
    distance_minimum: float
    distance_perfect: float


@dataclass
class MonthGoalCountApiModel:
    id: int
    workout_type: str
    year: int
    month: int
    count_minimum: int
    count_perfect: int


@dataclass
class MonthGoalDurationApiModel:
    id: int
    workout_type: str
    year: int
    month: int
    duration_minimum: int
    duration_perfect: int


@dataclass
class DistanceWorkoutApiModel:
    id: int
    workout_type: str
    name: str
    date: str
    start_time: str
    duration: int
    average_heart_rate: int
    participants: list[int]
    distance: int
    elevation_sum: int
    planned_tour_id: int
    has_gpx: bool
    custom_fields: dict[str, str | int | float]


@dataclass
class FitnessWorkoutApiModel:
    id: int
    workout_type: str
    name: str
    date: str
    start_time: str
    duration: int
    average_heart_rate: int
    participants: list[int]
    fitness_workout_type: str
    fitness_workout_categories: list[str]
    custom_fields: dict[str, str | int | float]


@dataclass
class ParticipantApiModel:
    id: int
    name: str


@dataclass
class PlannedTourApiModel:
    id: int
    workout_type: str
    name: str


@dataclass
class MaintenanceTourApiModel:
    id: int
    workout_type: str
    description: str
    is_reminder_active: bool
    reminder_limit: int
    is_reminder_triggered: bool
    limit_exceeded_distance: int


@dataclass
class CustomFieldApiModel:
    id: int
    workout_type: str
    field_type: str
    name: str
    is_required: bool
