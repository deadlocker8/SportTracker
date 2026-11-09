from collections.abc import Callable

from sporttracker.api.Models import (
    CustomFieldApiModel,
    DistanceWorkoutApiModel,
    EquipmentApiModel,
    FitnessWorkoutApiModel,
    MaintenanceApiModel,
    MonthGoalCountApiModel,
    MonthGoalDistanceApiModel,
    MonthGoalDurationApiModel,
    ParticipantApiModel,
    PlannedTourApiModel,
)
from sporttracker.equipment.bike.BikeEntity import Bike
from sporttracker.equipment.clothes.ClothesEntity import Clothes
from sporttracker.equipment.custom.CustomEquipmentEntity import CustomEquipment
from sporttracker.equipment.EquipmentEntity import Equipment
from sporttracker.equipment.EquipmentType import EquipmentType
from sporttracker.helpers import DateFormats
from sporttracker.maintenance.MaintenanceEventsCollector import MaintenanceWithEventsModel
from sporttracker.monthGoal.MonthGoalEntity import MonthGoalCount, MonthGoalDistance, MonthGoalDuration
from sporttracker.plannedTour.PlannedTourEntity import PlannedTour
from sporttracker.user.CustomWorkoutFieldEntity import CustomWorkoutField
from sporttracker.user.ParticipantEntity import Participant
from sporttracker.workout.distance.DistanceWorkoutEntity import DistanceWorkout
from sporttracker.workout.fitness.FitnessWorkoutEntity import FitnessWorkout


class Mapper:
    def __init__(self, source_types: list[type], target_type: type, mappings: dict[str, Callable]) -> None:
        self._source_types = source_types
        self._target_type = target_type
        self._mappings = mappings

    def map(self, source: object) -> object:
        if type(source) not in self._source_types:
            raise ValueError(
                f'Could not map {type(source)} to {self._target_type}: Source is not of type {self._source_types}'
            )

        properties = {}
        for target_name, mapping in self._mappings.items():
            properties[target_name] = mapping(source)

        return self._target_type(**properties)


MAPPER_MONTH_GOAL_DISTANCE = Mapper(
    [MonthGoalDistance],
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
    [MonthGoalCount],
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
    [MonthGoalDuration],
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
    [DistanceWorkout],
    DistanceWorkoutApiModel,
    {
        'id': lambda source: source.id,
        'workout_type': lambda source: source.type.name,
        'date': lambda source: source.start_time.strftime(DateFormats.DATE_FORMAT_DATE),
        'start_time': lambda source: source.start_time.strftime(DateFormats.DATE_FORMAT_TIME),
        'name': lambda source: source.name,
        'duration': lambda source: source.duration,
        'average_heart_rate': lambda source: source.average_heart_rate,
        'participants': lambda source: [item.id for item in source.participants],
        'equipment': lambda source: [item.id for item in source.equipment],
        'distance': lambda source: source.distance,
        'elevation_sum': lambda source: source.elevation_sum,
        'planned_tour_id': lambda source: source.planned_tour.id if source.planned_tour else None,
        'has_gpx': lambda source: source.get_gpx_metadata() is not None,
        'custom_fields': lambda source: source.custom_fields,
    },
)

MAPPER_FITNESS_WORKOUT = Mapper(
    [FitnessWorkout],
    FitnessWorkoutApiModel,
    {
        'id': lambda source: source.id,
        'workout_type': lambda source: source.type.name,
        'date': lambda source: source.start_time.strftime(DateFormats.DATE_FORMAT_DATE),
        'start_time': lambda source: source.start_time.strftime(DateFormats.DATE_FORMAT_TIME),
        'name': lambda source: source.name,
        'duration': lambda source: source.duration,
        'average_heart_rate': lambda source: source.average_heart_rate,
        'participants': lambda source: [item.id for item in source.participants],
        'equipment': lambda source: [item.id for item in source.equipment],
        'fitness_workout_type': lambda source: source.fitness_workout_type.name,
        'fitness_workout_categories': lambda source: [c.name for c in source.get_workout_categories()],
        'custom_fields': lambda source: source.custom_fields,
    },
)

MAPPER_PARTICIPANT = Mapper(
    [Participant],
    ParticipantApiModel,
    {
        'id': lambda source: source.id,
        'name': lambda source: source.name,
    },
)


def _get_equipment_type(equipment: Equipment) -> str:
    if isinstance(equipment, Bike):
        return EquipmentType.BIKE.name
    elif isinstance(equipment, Clothes):
        return EquipmentType.CLOTHES.name
    elif isinstance(equipment, CustomEquipment):
        return EquipmentType.CUSTOM.name

    raise ValueError(f'Could not determine equipment type for: {equipment}')


MAPPER_EQUIPMENT = Mapper(
    [Equipment, Bike, Clothes, CustomEquipment],
    EquipmentApiModel,
    {
        'id': lambda source: source.id,
        'workout_type': lambda source: source.workout_type.name,
        'equipment_type': lambda source: _get_equipment_type(source),  # type: ignore[arg-type]
        'name': lambda source: source.name,
        'purchase_date': lambda source: (
            source.purchase_date.strftime(DateFormats.DATE_FORMAT_DATE) if source.purchase_date else None
        ),
        'is_active': lambda source: source.is_active,
        'inactive_date': lambda source: (
            source.inactive_date.strftime(DateFormats.DATE_FORMAT_DATE) if source.inactive_date else None
        ),
        'clothes_type': lambda source: (
            source.clothes_type.name if isinstance(source, Clothes) and source.clothes_type else None
        ),
    },
)

MAPPER_PLANNED_TOUR = Mapper(
    [PlannedTour],
    PlannedTourApiModel,
    {
        'id': lambda source: source.id,
        'workout_type': lambda source: source.type.name,
        'name': lambda source: source.name,
    },
)

MAPPER_MAINTENANCE = Mapper(
    [MaintenanceWithEventsModel],
    MaintenanceApiModel,
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
    [CustomWorkoutField],
    CustomFieldApiModel,
    {
        'id': lambda source: source.id,
        'workout_type': lambda source: source.workout_type.name,
        'field_type': lambda source: source.type.name,
        'name': lambda source: source.name,
        'is_required': lambda source: source.is_required,
    },
)
