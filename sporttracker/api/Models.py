from dataclasses import dataclass


@dataclass
class MonthGoalDistanceModel:
    id: int
    workout_type: str
    year: int
    month: int
    distance_minimum: float
    distance_perfect: float


@dataclass
class MonthGoalCountModel:
    id: int
    workout_type: str
    year: int
    month: int
    count_minimum: int
    count_perfect: int


@dataclass
class MonthGoalDurationModel:
    id: int
    workout_type: str
    year: int
    month: int
    duration_minimum: int
    duration_perfect: int
