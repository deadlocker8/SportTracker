from dataclasses import dataclass
from datetime import datetime
from operator import attrgetter

import natsort
from natsort import natsorted

from sporttracker.maintenance.MaintenanceEventInstanceBlueprint import MaintenanceEventInstanceModel
from sporttracker.logic.model.CustomWorkoutField import get_custom_field_by_id
from sporttracker.logic.model.DistanceWorkout import get_distance_between_dates
from sporttracker.maintenance.MaintenanceEntity import Maintenance
from sporttracker.maintenance.MaintenanceEventInstanceEntity import (
    MaintenanceEventInstance,
    get_maintenance_events_by_maintenance_id,
)
from sporttracker.logic.model.WorkoutType import WorkoutType
from sporttracker.maintenance.MaintenanceFilterStateEntity import MaintenanceFilterState
from sporttracker.logic.model.filterStates.QuickFilterState import QuickFilterState


@dataclass
class MaintenanceWithEventsModel:
    id: int
    type: WorkoutType
    description: str
    isLimitActive: bool
    limit: int
    isLimitExceeded: bool
    limitExceededDistance: int | None
    events: list[MaintenanceEventInstanceModel]
    custom_workout_field_name: str | None
    custom_workout_field_value: str | None


def get_maintenances_with_events(
    quickFilterState: QuickFilterState, maintenanceFilterState: MaintenanceFilterState, user_id: int
) -> list[MaintenanceWithEventsModel]:
    maintenanceQuery = Maintenance.query.filter(Maintenance.user_id == user_id)

    if maintenanceFilterState.custom_workout_field_id and maintenanceFilterState.custom_workout_field_value is not None:
        maintenanceQuery = maintenanceQuery.filter(
            Maintenance.custom_workout_field_id == maintenanceFilterState.custom_workout_field_id
        ).filter(Maintenance.custom_workout_field_value == maintenanceFilterState.custom_workout_field_value)

    maintenanceList = maintenanceQuery.all()
    maintenanceList = natsorted(maintenanceList, alg=natsort.ns.IGNORECASE, key=attrgetter('description'))

    maintenancesWithEvents: list[MaintenanceWithEventsModel] = []
    for maintenance in maintenanceList:
        if maintenance.type not in quickFilterState.get_active_workout_types():
            continue

        model = create_maintenance_model(maintenance)
        maintenancesWithEvents.append(model)

    return maintenancesWithEvents


def create_maintenance_model(maintenance: Maintenance) -> MaintenanceWithEventsModel:
    events: list[MaintenanceEventInstance] = get_maintenance_events_by_maintenance_id(
        maintenance.id, maintenance.user_id
    )

    eventModels: list[MaintenanceEventInstanceModel] = __convert_events_to_models(events, maintenance)

    isLimitExceeded = False
    limitExceededDistance = None
    if maintenance.is_reminder_active and eventModels:
        distanceUntilToday = eventModels[-1].distanceSinceEvent or 0
        if distanceUntilToday >= maintenance.reminder_limit:
            isLimitExceeded = True
            limitExceededDistance = distanceUntilToday - maintenance.reminder_limit

    customWorkoutField = get_custom_field_by_id(maintenance.custom_workout_field_id, maintenance.user_id)
    customWorkoutFieldName = None if customWorkoutField is None else customWorkoutField.name

    return MaintenanceWithEventsModel(
        id=maintenance.id,
        type=maintenance.type,
        description=maintenance.description,  # type: ignore[arg-type]
        isLimitActive=maintenance.is_reminder_active,
        limit=maintenance.reminder_limit,
        isLimitExceeded=isLimitExceeded,
        limitExceededDistance=limitExceededDistance,
        events=eventModels,
        custom_workout_field_name=customWorkoutFieldName,  # type: ignore[arg-type]
        custom_workout_field_value=maintenance.custom_workout_field_value,  # type: ignore[arg-type]
    )


def __convert_events_to_models(
    events: list[MaintenanceEventInstance], maintenance: Maintenance
) -> list[MaintenanceEventInstanceModel]:
    if not events:
        return []

    eventModels: list[MaintenanceEventInstanceModel] = []
    customWorkoutField = get_custom_field_by_id(maintenance.custom_workout_field_id, maintenance.user_id)
    customWorkoutFieldName = None if customWorkoutField is None else customWorkoutField.name

    previousEventDate = events[0].event_date
    for event in events:
        distanceSinceEvent = get_distance_between_dates(
            maintenance.user_id,
            previousEventDate,
            event.event_date,
            [maintenance.type],
            customWorkoutFieldName,  # type: ignore[arg-type]
            maintenance.custom_workout_field_value,  # type: ignore[arg-type]
        )
        numberOfDaysSinceEvent = (event.event_date - previousEventDate).days  # type: ignore[operator]
        previousEventDate = event.event_date

        eventModel = MaintenanceEventInstanceModel.create_from_event(event)
        eventModel.distanceSinceEvent = distanceSinceEvent
        eventModel.numberOfDaysSinceEvent = numberOfDaysSinceEvent
        eventModels.append(eventModel)

    # add additional pseudo maintenance event representing today
    now = datetime.now()
    distanceUntilToday = get_distance_between_dates(
        maintenance.user_id,
        previousEventDate,
        now,
        [maintenance.type],
        customWorkoutFieldName,  # type: ignore[arg-type]
        maintenance.custom_workout_field_value,  # type: ignore[arg-type]
    )

    eventModels.append(
        MaintenanceEventInstanceModel(
            id=None,
            eventDate=now,  # type: ignore[arg-type]
            date=None,
            time=None,
            distanceSinceEvent=distanceUntilToday,
            numberOfDaysSinceEvent=(now - previousEventDate).days,  # type: ignore[operator]
        )
    )

    return eventModels
