from typing import Callable, Type

from sporttracker.api.Models import (
    MonthGoalDistanceApiModel,
    MonthGoalCountApiModel,
    MonthGoalDurationApiModel,
    DistanceWorkoutApiModel,
    FitnessWorkoutApiModel,
    ParticipantApiModel,
    PlannedTourApiModel,
    MaintenanceTourApiModel,
    CustomFieldApiModel,
)
from sporttracker.logic.MaintenanceEventsCollector import MaintenanceWithEventsModel
from sporttracker.logic.model.CustomWorkoutField import CustomWorkoutField
from sporttracker.logic.model.DistanceWorkout import DistanceWorkout
from sporttracker.logic.model.FitnessWorkout import FitnessWorkout
from sporttracker.logic.model.MonthGoal import MonthGoalDistance, MonthGoalCount, MonthGoalDuration
from sporttracker.logic.model.Participant import Participant
from sporttracker.logic.model.PlannedTour import PlannedTour


class Mapper:
    def __init__(self, source_type: Type, target_type: Type, mappings: dict[str, Callable]) -> None:
        self._source_type = source_type
        self._target_type = target_type
        self._mappings = mappings

    def map(self, source: object) -> object:
        if type(source) is not self._source_type:
            raise ValueError(
                f'Could not map {self._source_type} to {self._target_type}: Source is not of type {self._source_type}'
            )

        properties = {}
        for target_name, mapping in self._mappings.items():
            properties[target_name] = mapping(source)

        return self._target_type(**properties)


MAPPER_MONTH_GOAL_DISTANCE = Mapper(
    MonthGoalDistance,
    MonthGoalDistanceApiModel,
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
    MonthGoalCountApiModel,
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
    MonthGoalDurationApiModel,
    {
        'id': lambda source: source.id,
        'workout_type': lambda source: source.type.name,
        'year': lambda source: source.year,
        'month': lambda source: source.month,
        'duration_minimum': lambda source: source.duration_minimum,
        'duration_perfect': lambda source: source.duration_perfect,
    },
)

MAPPER_DISTANCE_WORKOUT = Mapper(
    DistanceWorkout,
    DistanceWorkoutApiModel,
    {
        'id': lambda source: source.id,
        'workout_type': lambda source: source.type.name,
        'date': lambda source: source.start_time.strftime('%Y-%m-%d'),
        'start_time': lambda source: source.start_time.strftime('%H:%M'),
        'name': lambda source: source.name,
        'duration': lambda source: source.duration,
        'average_heart_rate': lambda source: source.average_heart_rate,
        'participants': lambda source: [item.id for item in source.participants],
        'distance': lambda source: source.distance,
        'elevation_sum': lambda source: source.elevation_sum,
        'planned_tour_id': lambda source: source.planned_tour.id if source.planned_tour else None,
        'has_gpx': lambda source: source.get_gpx_metadata() is not None,
        'custom_fields': lambda source: source.custom_fields,
    },
)

MAPPER_FITNESS_WORKOUT = Mapper(
    FitnessWorkout,
    FitnessWorkoutApiModel,
    {
        'id': lambda source: source.id,
        'workout_type': lambda source: source.type.name,
        'date': lambda source: source.start_time.strftime('%Y-%m-%d'),
        'start_time': lambda source: source.start_time.strftime('%H:%M'),
        'name': lambda source: source.name,
        'duration': lambda source: source.duration,
        'average_heart_rate': lambda source: source.average_heart_rate,
        'participants': lambda source: [item.id for item in source.participants],
        'fitness_workout_type': lambda source: source.fitness_workout_type.name,
        'fitness_workout_categories': lambda source: [c.name for c in source.get_workout_categories()],
        'custom_fields': lambda source: source.custom_fields,
    },
)

MAPPER_PARTICIPANT = Mapper(
    Participant,
    ParticipantApiModel,
    {
        'id': lambda source: source.id,
        'name': lambda source: source.name,
    },
)

MAPPER_PLANNED_TOUR = Mapper(
    PlannedTour,
    PlannedTourApiModel,
    {
        'id': lambda source: source.id,
        'workout_type': lambda source: source.type.name,
        'name': lambda source: source.name,
    },
)

MAPPER_MAINTENANCE = Mapper(
    MaintenanceWithEventsModel,
    MaintenanceTourApiModel,
    {
        'id': lambda source: source.id,
        'workout_type': lambda source: source.type.name,
        'description': lambda source: source.description,
        'is_reminder_active': lambda source: source.isLimitActive,
        'reminder_limit': lambda source: source.limit,
        'is_reminder_triggered': lambda source: source.isLimitExceeded,
        'limit_exceeded_distance': lambda source: source.limitExceededDistance,
    },
)

MAPPER_CUSTOM_FIELD = Mapper(
    CustomWorkoutField,
    CustomFieldApiModel,
    {
        'id': lambda source: source.id,
        'workout_type': lambda source: source.workout_type.name,
        'field_type': lambda source: source.type.name,
        'name': lambda source: source.name,
        'is_required': lambda source: source.is_required,
    },
)
