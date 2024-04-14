import logging
from dataclasses import dataclass
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, abort
from flask_login import login_required, current_user
from flask_pydantic import validate
from pydantic import BaseModel

from sporttracker.logic import Constants
from sporttracker.logic.QuickFilterState import get_quick_filter_state_from_session
from sporttracker.logic.model.MaintenanceEvent import MaintenanceEvent
from sporttracker.logic.model.Track import TrackType
from sporttracker.logic.model.db import db

LOGGER = logging.getLogger(Constants.APP_NAME)


@dataclass
class MaintenanceEventModel:
    id: int
    eventDate: datetime
    date: str
    time: str
    type: TrackType
    description: str


class MaintenanceEventFormModel(BaseModel):
    date: str
    time: str
    type: str
    description: str

    def calculate_event_date(self) -> datetime:
        return datetime.strptime(f'{self.date} {self.time}', '%Y-%m-%d %H:%M')


def construct_blueprint():
    maintenanceEvents = Blueprint('maintenanceEvents', __name__, static_folder='static',
                                  url_prefix='/maintenanceEvents')

    @maintenanceEvents.route('/')
    @login_required
    def listMaintenanceEvents():
        quickFilterState = get_quick_filter_state_from_session()

        events: list[MaintenanceEvent] = (
            MaintenanceEvent.query
            .filter(MaintenanceEvent.user_id == current_user.id)
            .filter(MaintenanceEvent.type.in_(quickFilterState.get_active_types()))
            .all())

        maintenanceEventList = []
        for event in events:
            maintenanceEventList.append(
                MaintenanceEventModel(event.id, event.event_date, event.get_date(), event.get_time(), event.type,
                                      event.description))

        return render_template('maintenanceEvents/maintenanceEvents.jinja2',
                               maintenanceEvents=maintenanceEventList,
                               quickFilterState=quickFilterState)

    @maintenanceEvents.route('/add')
    @login_required
    def add():
        return render_template('maintenanceEvents/maintenanceEventForm.jinja2')

    @maintenanceEvents.route('/post', methods=['POST'])
    @login_required
    @validate()
    def addPost(form: MaintenanceEventFormModel):
        maintenanceEvent = MaintenanceEvent(
            event_date=form.calculate_event_date(),
            type=TrackType(form.type),  # type: ignore[call-arg]
            description=form.description,
            user_id=current_user.id
        )

        LOGGER.debug(f'Saved new maintenance event: {maintenanceEvent}')
        db.session.add(maintenanceEvent)
        db.session.commit()

        return redirect(url_for('maintenanceEvents.listMaintenanceEvents'))

    @maintenanceEvents.route('/edit/<int:event_id>')
    @login_required
    def edit(event_id: int):
        maintenanceEvent = (
            MaintenanceEvent.query
            .filter(MaintenanceEvent.user_id == current_user.id)
            .filter(MaintenanceEvent.id == event_id)
            .first()
        )

        if maintenanceEvent is None:
            abort(404)

        eventModel = MaintenanceEventModel(
            id=maintenanceEvent.id,
            eventDate=maintenanceEvent.event_date,
            date=maintenanceEvent.get_date(),
            time=maintenanceEvent.get_time(),
            type=maintenanceEvent.type.name,
            description=maintenanceEvent.description,
        )

        return render_template(
            'maintenanceEvents/maintenanceEventForm.jinja2', maintenanceEvent=eventModel, event_id=event_id
        )

    @maintenanceEvents.route('/edit/<int:event_id>', methods=['POST'])
    @login_required
    @validate()
    def editPost(event_id: int, form: MaintenanceEventFormModel):
        maintenanceEvent = (
            MaintenanceEvent.query
            .filter(MaintenanceEvent.user_id == current_user.id)
            .filter(MaintenanceEvent.id == event_id)
            .first()
        )

        if maintenanceEvent is None:
            abort(404)

        maintenanceEvent.type = TrackType(form.type)  # type: ignore[call-arg]
        maintenanceEvent.event_date = form.calculate_event_date()
        maintenanceEvent.description = form.description
        maintenanceEvent.user_id = current_user.id

        LOGGER.debug(f'Updated maintenance event: {maintenanceEvent}')
        db.session.commit()

        return redirect(url_for('maintenanceEvents.listMaintenanceEvents'))

    @maintenanceEvents.route('/delete/<int:event_id>')
    @login_required
    def delete(event_id: int):
        maintenanceEvent = (
            MaintenanceEvent.query
            .filter(MaintenanceEvent.user_id == current_user.id)
            .filter(MaintenanceEvent.id == event_id)
            .first()
        )

        if maintenanceEvent is None:
            abort(404)

        LOGGER.debug(f'Deleted maintenance event: {maintenanceEvent}')
        db.session.delete(maintenanceEvent)
        db.session.commit()

        return redirect(url_for('maintenanceEvents.listMaintenanceEvents'))

    return maintenanceEvents
