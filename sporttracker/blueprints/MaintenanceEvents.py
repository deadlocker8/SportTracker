import logging
from dataclasses import dataclass
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, abort
from flask_login import login_required, current_user
from flask_pydantic import validate
from pydantic import BaseModel

from sporttracker.logic import Constants
from sporttracker.logic.QuickFilterState import get_quick_filter_state_from_session
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
    distanceSinceEvent: int
    numberOfDaysSinceEvent: int


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

        eventDescriptions: list[str] = (
            MaintenanceEvent.query.with_entities(MaintenanceEvent.description)
            .filter(MaintenanceEvent.user_id == current_user.id)
            .filter(MaintenanceEvent.type.in_(quickFilterState.get_active_types()))
            .distinct()
            .all()
        )
        eventDescriptions = [d[0] for d in eventDescriptions]

        maintenanceEventsByDescription: dict[str, dict[TrackType, list[MaintenanceEventModel]]] = {}
        for description in eventDescriptions:
            maintenanceEventsByDescription[description] = {}

            for trackType in TrackType:
                events: list[MaintenanceEvent] = (
                    MaintenanceEvent.query.filter(MaintenanceEvent.user_id == current_user.id)
                    .filter(MaintenanceEvent.type.in_(quickFilterState.get_active_types()))
                    .filter(MaintenanceEvent.type == trackType)
                    .filter(MaintenanceEvent.description == description)
                    .order_by(MaintenanceEvent.event_date.asc())
                    .all()
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

                    maintenanceEventsByDescription[description][trackType].append(
                        MaintenanceEventModel(
                            event.id,
                            event.event_date,  # type: ignore[arg-type]
                            event.get_date(),
                            event.get_time(),
                            event.type,
                            event.description,  # type: ignore[arg-type]
                            distanceSinceEvent,
                            numberOfDaysSinceEvent,
                        )
                    )

                now = datetime.now()
                distanceUntilToday = get_distance_between_dates(event.event_date, now, [event.type])

                maintenanceEventsByDescription[description][trackType].append(
                    MaintenanceEventModel(
                        None,
                        now,  # type: ignore[arg-type]
                        None,
                        None,
                        events[0].type,
                        description,  # type: ignore[arg-type]
                        distanceUntilToday,
                        (now - event.event_date).days,  # type: ignore[operator]
                    )
                )

        return render_template(
            'maintenanceEvents/maintenanceEvents.jinja2',
            maintenanceEventsByDescription=maintenanceEventsByDescription,
            quickFilterState=quickFilterState,
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
            distanceSinceEvent=0,
            numberOfDaysSinceEvent=0,
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
            distanceSinceEvent=0,
            numberOfDaysSinceEvent=0,
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
