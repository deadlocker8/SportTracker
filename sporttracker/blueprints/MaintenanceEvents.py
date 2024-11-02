from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, abort
from flask_login import login_required, current_user
from flask_pydantic import validate
from pydantic import BaseModel

from sporttracker.logic import Constants
from sporttracker.logic.QuickFilterState import (
    get_quick_filter_state_from_session,
    QuickFilterState,
)
from sporttracker.logic.model.MaintenanceEvent import MaintenanceEvent, get_maintenance_event_by_id
from sporttracker.logic.model.Track import get_distance_between_dates
from sporttracker.logic.model.TrackType import TrackType
from sporttracker.logic.model.db import db

LOGGER = logging.getLogger(Constants.APP_NAME)


@dataclass
class MaintenanceEventModel:
    id: int | None
    eventDate: datetime | None
    date: str | None
    time: str | None
    type: TrackType
    description: str
    distanceSinceEvent: int | None = None
    numberOfDaysSinceEvent: int | None = None

    @staticmethod
    def create_from_event(event: MaintenanceEvent) -> MaintenanceEventModel:
        return MaintenanceEventModel(
            id=event.id,
            eventDate=event.event_date,  # type: ignore[arg-type]
            date=event.get_date(),
            time=event.get_time(),
            type=event.type,
            description=event.description,  # type: ignore[arg-type]
        )


class MaintenanceEventFormModel(BaseModel):
    date: str
    time: str
    type: str
    description: str

    def calculate_event_date(self) -> datetime:
        return datetime.strptime(f'{self.date} {self.time}', '%Y-%m-%d %H:%M')


def construct_blueprint():
    maintenanceEvents = Blueprint(
        'maintenanceEvents', __name__, static_folder='static', url_prefix='/maintenanceEvents'
    )

    @maintenanceEvents.route('/')
    @login_required
    def listMaintenanceEvents():
        quickFilterState = get_quick_filter_state_from_session()

        availableEventDescriptions: list[str] = __get_all_event_descriptions(quickFilterState)

        maintenanceEventsByDescription: dict[str, dict[TrackType, list[MaintenanceEventModel]]] = {}
        for description in availableEventDescriptions:
            maintenanceEventsByDescription[description] = {}

            for trackType in TrackType:
                events: list[MaintenanceEvent] = __get_maintenance_events_by_description_and_type(
                    description, quickFilterState, trackType
                )

                if not events:
                    continue

                maintenanceEventsByDescription[description][trackType] = []

                previousEventDate = events[0].event_date
                for event in events:
                    distanceSinceEvent = get_distance_between_dates(
                        previousEventDate, event.event_date, [event.type]
                    )
                    numberOfDaysSinceEvent = (event.event_date - previousEventDate).days  # type: ignore[operator]
                    previousEventDate = event.event_date

                    eventModel = MaintenanceEventModel.create_from_event(event)
                    eventModel.distanceSinceEvent = distanceSinceEvent
                    eventModel.numberOfDaysSinceEvent = numberOfDaysSinceEvent
                    maintenanceEventsByDescription[description][trackType].append(eventModel)

                # add additional pseudo maintenance event representing today
                now = datetime.now()
                distanceUntilToday = get_distance_between_dates(previousEventDate, now, [trackType])

                maintenanceEventsByDescription[description][trackType].append(
                    MaintenanceEventModel(
                        id=None,
                        eventDate=now,  # type: ignore[arg-type]
                        date=None,
                        time=None,
                        type=events[0].type,
                        description=description,  # type: ignore[arg-type]
                        distanceSinceEvent=distanceUntilToday,
                        numberOfDaysSinceEvent=(now - previousEventDate).days,  # type: ignore[operator]
                    )
                )

        return render_template(
            'maintenanceEvents/maintenanceEvents.jinja2',
            maintenanceEventsByDescription=maintenanceEventsByDescription,
            quickFilterState=quickFilterState,
        )

    def __get_all_event_descriptions(quickFilterState: QuickFilterState) -> list[str]:
        availableEventDescriptions = (
            MaintenanceEvent.query.with_entities(MaintenanceEvent.description)
            .filter(MaintenanceEvent.user_id == current_user.id)
            .filter(MaintenanceEvent.type.in_(quickFilterState.get_active_types()))
            .distinct()
            .all()
        )

        return [d[0] for d in availableEventDescriptions]

    def __get_maintenance_events_by_description_and_type(
        description: str, quickFilterState: QuickFilterState, trackType: TrackType
    ) -> list[MaintenanceEvent]:
        return (
            MaintenanceEvent.query.filter(MaintenanceEvent.user_id == current_user.id)
            .filter(MaintenanceEvent.type.in_(quickFilterState.get_active_types()))
            .filter(MaintenanceEvent.type == trackType)
            .filter(MaintenanceEvent.description == description)
            .order_by(MaintenanceEvent.event_date.asc())
            .all()
        )

    @maintenanceEvents.route('/add')
    @login_required
    def add():
        return render_template('maintenanceEvents/maintenanceEventForm.jinja2')

    @maintenanceEvents.route('/addByTypeAndDescription/<string:track_type>/<string:description>')
    @login_required
    def addByTypeAndDescription(track_type: str, description: str):
        trackType = TrackType(track_type)  # type: ignore[call-arg]

        eventModel = MaintenanceEventModel(
            id=None,
            eventDate=None,
            date=None,
            time=None,
            type=trackType.name,  # type: ignore[arg-type]
            description=description,
        )
        return render_template(
            'maintenanceEvents/maintenanceEventForm.jinja2',
            maintenanceEvent=eventModel,
        )

    @maintenanceEvents.route('/post', methods=['POST'])
    @login_required
    @validate()
    def addPost(form: MaintenanceEventFormModel):
        maintenanceEvent = MaintenanceEvent(
            event_date=form.calculate_event_date(),
            type=TrackType(form.type),  # type: ignore[call-arg]
            description=form.description,
            user_id=current_user.id,
        )

        LOGGER.debug(f'Saved new maintenance event: {maintenanceEvent}')
        db.session.add(maintenanceEvent)
        db.session.commit()

        return redirect(url_for('maintenanceEvents.listMaintenanceEvents'))

    @maintenanceEvents.route('/edit/<int:event_id>')
    @login_required
    def edit(event_id: int):
        maintenanceEvent = get_maintenance_event_by_id(event_id)

        if maintenanceEvent is None:
            abort(404)

        eventModel = MaintenanceEventModel(
            id=maintenanceEvent.id,
            eventDate=maintenanceEvent.event_date,  # type: ignore[arg-type]
            date=maintenanceEvent.get_date(),
            time=maintenanceEvent.get_time(),
            type=maintenanceEvent.type.name,
            description=maintenanceEvent.description,  # type: ignore[arg-type]
        )

        return render_template(
            'maintenanceEvents/maintenanceEventForm.jinja2',
            maintenanceEvent=eventModel,
            event_id=event_id,
        )

    @maintenanceEvents.route('/edit/<int:event_id>', methods=['POST'])
    @login_required
    @validate()
    def editPost(event_id: int, form: MaintenanceEventFormModel):
        maintenanceEvent = get_maintenance_event_by_id(event_id)

        if maintenanceEvent is None:
            abort(404)

        maintenanceEvent.type = TrackType(form.type)  # type: ignore[call-arg]
        maintenanceEvent.event_date = form.calculate_event_date()  # type: ignore[assignment]
        maintenanceEvent.description = form.description  # type: ignore[assignment]
        maintenanceEvent.user_id = current_user.id

        LOGGER.debug(f'Updated maintenance event: {maintenanceEvent}')
        db.session.commit()

        return redirect(url_for('maintenanceEvents.listMaintenanceEvents'))

    @maintenanceEvents.route('/delete/<int:event_id>')
    @login_required
    def delete(event_id: int):
        maintenanceEvent = get_maintenance_event_by_id(event_id)

        if maintenanceEvent is None:
            abort(404)

        LOGGER.debug(f'Deleted maintenance event: {maintenanceEvent}')
        db.session.delete(maintenanceEvent)
        db.session.commit()

        return redirect(url_for('maintenanceEvents.listMaintenanceEvents'))

    return maintenanceEvents
