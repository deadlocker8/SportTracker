import logging
from dataclasses import dataclass
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, abort
from flask_login import login_required, current_user
from flask_pydantic import validate
from pydantic import BaseModel

from sporttracker.blueprints.MaintenanceEventInstances import MaintenanceEventInstanceModel
from sporttracker.logic import Constants
from sporttracker.logic.QuickFilterState import (
    get_quick_filter_state_from_session,
)
from sporttracker.logic.model.Maintenance import Maintenance, get_maintenance_by_id
from sporttracker.logic.model.MaintenanceEventInstance import (
    get_maintenance_events_by_maintenance_id,
    MaintenanceEventInstance,
)
from sporttracker.logic.model.Track import get_distance_between_dates
from sporttracker.logic.model.TrackType import TrackType
from sporttracker.logic.model.db import db

LOGGER = logging.getLogger(Constants.APP_NAME)


@dataclass
class MaintenanceModel:
    id: int | None
    type: TrackType
    description: str


class MaintenanceFormModel(BaseModel):
    type: str
    description: str


@dataclass
class MaintenanceWithEventsModel:
    id: int
    type: TrackType
    description: str
    events: list[MaintenanceEventInstanceModel]


def construct_blueprint():
    maintenances = Blueprint(
        'maintenances', __name__, static_folder='static', url_prefix='/maintenances'
    )

    @maintenances.route('/')
    @login_required
    def listMaintenances():
        quickFilterState = get_quick_filter_state_from_session()

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

            eventModels: list[MaintenanceEventInstanceModel] = []

            if events:
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
                distanceUntilToday = get_distance_between_dates(
                    previousEventDate, now, [maintenance.type]
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

            model = MaintenanceWithEventsModel(
                id=maintenance.id,
                type=maintenance.type,
                description=maintenance.description,
                events=eventModels,
            )

            maintenancesWithEvents.append(model)

        return render_template(
            'maintenances/maintenances.jinja2',
            maintenancesWithEvents=maintenancesWithEvents,
            quickFilterState=quickFilterState,
        )

    @maintenances.route('/add')
    @login_required
    def add():
        return render_template('maintenances/maintenanceForm.jinja2')

    @maintenances.route('/post', methods=['POST'])
    @login_required
    @validate()
    def addPost(form: MaintenanceFormModel):
        maintenance = Maintenance(
            type=TrackType(form.type),  # type: ignore[call-arg]
            description=form.description,
            user_id=current_user.id,
        )

        LOGGER.debug(f'Saved new maintenance: {maintenance}')
        db.session.add(maintenance)
        db.session.commit()

        return redirect(url_for('maintenances.listMaintenances'))

    @maintenances.route('/edit/<int:maintenance_id>')
    @login_required
    def edit(maintenance_id: int):
        maintenance = get_maintenance_by_id(maintenance_id)

        if maintenance is None:
            abort(404)

        model = MaintenanceModel(
            id=maintenance.id,
            type=maintenance.type.name,
            description=maintenance.description,  # type: ignore[arg-type]
        )

        return render_template(
            'maintenances/maintenanceForm.jinja2',
            maintenance=model,
            maintenance_id=maintenance_id,
        )

    @maintenances.route('/edit/<int:maintenance_id>', methods=['POST'])
    @login_required
    @validate()
    def editPost(maintenance_id: int, form: MaintenanceFormModel):
        maintenance = get_maintenance_by_id(maintenance_id)

        if maintenance is None:
            abort(404)

        maintenance.type = TrackType(form.type)  # type: ignore[call-arg]
        maintenance.description = form.description  # type: ignore[assignment]
        maintenance.user_id = current_user.id

        LOGGER.debug(f'Updated maintenance: {maintenance}')
        db.session.commit()

        return redirect(url_for('maintenances.listMaintenances'))

    @maintenances.route('/delete/<int:maintenance_id>')
    @login_required
    def delete(maintenance_id: int):
        maintenance = get_maintenance_by_id(maintenance_id)

        if maintenance is None:
            abort(404)

        events = get_maintenance_events_by_maintenance_id(maintenance_id)
        for event in events:
            LOGGER.debug(f'Deleted maintenance event: {event}')
            db.session.delete(event)

        db.session.commit()

        LOGGER.debug(f'Deleted maintenance: {maintenance} and {len(events)} events')
        db.session.delete(maintenance)
        db.session.commit()

        return redirect(url_for('maintenances.listMaintenances'))

    return maintenances
