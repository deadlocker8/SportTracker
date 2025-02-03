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
