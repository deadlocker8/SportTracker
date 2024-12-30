from dataclasses import dataclass
from datetime import datetime

from flask_login import current_user

from sporttracker.blueprints.MaintenanceEventInstances import MaintenanceEventInstanceModel
from sporttracker.logic.QuickFilterState import QuickFilterState
from sporttracker.logic.model.Maintenance import Maintenance
from sporttracker.logic.model.MaintenanceEventInstance import (
    MaintenanceEventInstance,
    get_maintenance_events_by_maintenance_id,
)
from sporttracker.logic.model.Track import get_distance_between_dates
from sporttracker.logic.model.TrackType import TrackType


@dataclass
class MaintenanceWithEventsModel:
    id: int
    type: TrackType
    description: str
    events: list[MaintenanceEventInstanceModel]


def get_maintenances_with_events(
    quickFilterState: QuickFilterState,
) -> list[MaintenanceWithEventsModel]:
    maintenanceList = (
        Maintenance.query.filter(Maintenance.user_id == current_user.id)
        .order_by(Maintenance.description.asc())
        .all()
    )

    maintenancesWithEvents: list[MaintenanceWithEventsModel] = []
    for maintenance in maintenanceList:
        if maintenance.type not in quickFilterState.get_active_types():
            continue

        events: list[MaintenanceEventInstance] = get_maintenance_events_by_maintenance_id(
            maintenance.id
        )

        eventModels: list[MaintenanceEventInstanceModel] = __convert_events_to_models(
            events, maintenance
        )

        model = MaintenanceWithEventsModel(
            id=maintenance.id,
            type=maintenance.type,
            description=maintenance.description,
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
        distanceSinceEvent = get_distance_between_dates(
            previousEventDate, event.event_date, [maintenance.type]
        )
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