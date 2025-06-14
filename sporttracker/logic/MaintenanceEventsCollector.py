from dataclasses import dataclass
from datetime import datetime
from operator import attrgetter

import natsort
from flask_login import current_user
from natsort import natsorted

from sporttracker.blueprints.MaintenanceEventInstances import MaintenanceEventInstanceModel
from sporttracker.logic.QuickFilterState import QuickFilterState
from sporttracker.logic.model.DistanceWorkout import get_distance_between_dates
from sporttracker.logic.model.Maintenance import Maintenance
from sporttracker.logic.model.MaintenanceEventInstance import (
    MaintenanceEventInstance,
    get_maintenance_events_by_maintenance_id,
    get_latest_maintenance_event_by_maintenance_id,
)
from sporttracker.logic.model.WorkoutType import WorkoutType


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


def get_maintenances_with_events(quickFilterState: QuickFilterState, user_id: int) -> list[MaintenanceWithEventsModel]:
    maintenanceList = Maintenance.query.filter(Maintenance.user_id == user_id).all()
    maintenanceList = natsorted(maintenanceList, alg=natsort.ns.IGNORECASE, key=attrgetter('description'))

    maintenancesWithEvents: list[MaintenanceWithEventsModel] = []
    for maintenance in maintenanceList:
        if maintenance.type not in quickFilterState.get_active_types():
            continue

        events: list[MaintenanceEventInstance] = get_maintenance_events_by_maintenance_id(maintenance.id, user_id)

        eventModels: list[MaintenanceEventInstanceModel] = __convert_events_to_models(events, maintenance)

        isLimitExceeded = False
        limitExceededDistance = None
        if maintenance.is_reminder_active and eventModels:
            distanceUntilToday = eventModels[-1].distanceSinceEvent
            if distanceUntilToday >= maintenance.reminder_limit:
                isLimitExceeded = True
                limitExceededDistance = distanceUntilToday - maintenance.reminder_limit

        model = MaintenanceWithEventsModel(
            id=maintenance.id,
            type=maintenance.type,
            description=maintenance.description,
            isLimitActive=maintenance.is_reminder_active,
            limit=maintenance.reminder_limit,
            isLimitExceeded=isLimitExceeded,
            limitExceededDistance=limitExceededDistance,
            events=eventModels,
        )

        maintenancesWithEvents.append(model)

    return maintenancesWithEvents


def __convert_events_to_models(
    events: list[MaintenanceEventInstance], maintenance: Maintenance
) -> list[MaintenanceEventInstanceModel]:
    if not events:
        return []

    eventModels: list[MaintenanceEventInstanceModel] = []

    previousEventDate = events[0].event_date
    for event in events:
        distanceSinceEvent = get_distance_between_dates(previousEventDate, event.event_date, [maintenance.type])
        numberOfDaysSinceEvent = (event.event_date - previousEventDate).days  # type: ignore[operator]
        previousEventDate = event.event_date

        eventModel = MaintenanceEventInstanceModel.create_from_event(event)
        eventModel.distanceSinceEvent = distanceSinceEvent
        eventModel.numberOfDaysSinceEvent = numberOfDaysSinceEvent
        eventModels.append(eventModel)

    # add additional pseudo maintenance event representing today
    now = datetime.now()
    distanceUntilToday = get_distance_between_dates(previousEventDate, now, [maintenance.type])

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


def get_number_of_triggered_maintenance_reminders() -> int:
    if not current_user.is_authenticated:
        return 0

    maintenanceList = Maintenance.query.filter(Maintenance.user_id == current_user.id).all()

    numberOfTriggeredMaintenanceReminders = 0
    for maintenance in maintenanceList:
        latestEvent: MaintenanceEventInstance | None = get_latest_maintenance_event_by_maintenance_id(maintenance.id)

        if latestEvent is None:
            continue

        now = datetime.now()
        distanceUntilToday = get_distance_between_dates(latestEvent.event_date, now, [maintenance.type])

        if not maintenance.is_reminder_active:
            continue

        if distanceUntilToday >= maintenance.reminder_limit:
            numberOfTriggeredMaintenanceReminders += 1

    return numberOfTriggeredMaintenanceReminders
