from typing import Callable, Type

from sporttracker.api.Models import (
    MonthGoalDistanceModel,
    MonthGoalCountModel,
    MonthGoalDurationModel,
)
from sporttracker.logic.model.MonthGoal import MonthGoalDistance, MonthGoalCount, MonthGoalDuration


class Mapper:
    def __init__(self, source_type: Type, target_type: Type, mappings: dict[str, Callable]) -> None:
        self._source_type = source_type
        self._target_type = target_type
        self._mappings = mappings

    def map(self, source: object) -> object:
        if type(source) is not self._source_type:
            raise ValueError(
                f'Could not map {self._source_type} to {self._target_type}: '
                f'Source is not of type {self._source_type}'
            )

        properties = {}
        for target_name, mapping in self._mappings.items():
            properties[target_name] = mapping(source)

        return self._target_type(**properties)


MAPPER_MONTH_GOAL_DISTANCE = Mapper(
    MonthGoalDistance,
    MonthGoalDistanceModel,
    {
        'id': lambda source: source.id,
        'workout_type': lambda source: source.type.name,
        'year': lambda source: source.year,
        'month': lambda source: source.month,
        'distance_minimum': lambda source: source.distance_minimum,
        'distance_perfect': lambda source: source.distance_perfect,
    },
)

MAPPER_MONTH_GOAL_COUNT = Mapper(
    MonthGoalCount,
    MonthGoalCountModel,
    {
        'id': lambda source: source.id,
        'workout_type': lambda source: source.type.name,
        'year': lambda source: source.year,
        'month': lambda source: source.month,
        'count_minimum': lambda source: source.count_minimum,
        'count_perfect': lambda source: source.count_perfect,
    },
)

MAPPER_MONTH_GOAL_DURATION = Mapper(
    MonthGoalDuration,
    MonthGoalDurationModel,
    {
        'id': lambda source: source.id,
        'workout_type': lambda source: source.type.name,
        'year': lambda source: source.year,
        'month': lambda source: source.month,
        'duration_minimum': lambda source: source.duration_minimum,
        'duration_perfect': lambda source: source.duration_perfect,
    },
)
