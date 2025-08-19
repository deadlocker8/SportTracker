import logging
from dataclasses import dataclass
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, abort
from flask_login import login_required
from flask_pydantic import validate
from pydantic import BaseModel

from sporttracker import Constants
from sporttracker.maintenance.MaintenanceEntity import get_maintenance_by_id
from sporttracker.maintenance.MaintenanceEventInstanceEntity import (
    get_maintenance_event_by_id,
    MaintenanceEventInstance,
)
from sporttracker.db import db

LOGGER = logging.getLogger(Constants.APP_NAME)


@dataclass
class MaintenanceEventInstanceModel:
    id: int | None
    eventDate: datetime | None
    date: str | None
    time: str | None
    distanceSinceEvent: int | None = None
    numberOfDaysSinceEvent: int | None = None

    @staticmethod
    def create_from_event(event: MaintenanceEventInstance) -> 'MaintenanceEventInstanceModel':
        return MaintenanceEventInstanceModel(
            id=event.id,
            eventDate=event.event_date,  # type: ignore[arg-type]
            date=event.get_date(),
            time=event.get_time(),
        )


class MaintenanceEventInstanceFormModel(BaseModel):
    date: str
    time: str

    def calculate_event_date(self) -> datetime:
        return datetime.strptime(f'{self.date} {self.time}', '%Y-%m-%d %H:%M')


def construct_blueprint():
    maintenanceEventInstances = Blueprint(
        'maintenanceEventInstances',
        __name__,
        static_folder='static',
        url_prefix='/maintenanceEventInstances',
    )

    @maintenanceEventInstances.route('/add/<int:maintenance_id>')
    @login_required
    def add(maintenance_id: int):
        maintenance = get_maintenance_by_id(maintenance_id)

        if maintenance is None:
            abort(404)

        return render_template('maintenanceEvent/maintenanceEventForm.jinja2', maintenance=maintenance)

    @maintenanceEventInstances.route('/post/<int:maintenance_id>', methods=['POST'])
    @login_required
    @validate()
    def addPost(maintenance_id: int, form: MaintenanceEventInstanceFormModel):
        maintenance = get_maintenance_by_id(maintenance_id)

        if maintenance is None:
            abort(404)

        maintenanceEvent = MaintenanceEventInstance(
            event_date=form.calculate_event_date(), maintenance_id=maintenance_id
        )

        LOGGER.debug(f'Saved new maintenance event: {maintenanceEvent}')
        db.session.add(maintenanceEvent)
        db.session.commit()

        return redirect(url_for('maintenances.listMaintenances'))

    @maintenanceEventInstances.route('/edit/<int:event_id>')
    @login_required
    def edit(event_id: int):
        maintenanceEvent = get_maintenance_event_by_id(event_id)

        if maintenanceEvent is None:
            abort(404)

        maintenance = get_maintenance_by_id(maintenanceEvent.maintenance_id)

        if maintenance is None:
            abort(404)

        eventModel = MaintenanceEventInstanceModel(
            id=maintenanceEvent.id,
            eventDate=maintenanceEvent.event_date,  # type: ignore[arg-type]
            date=maintenanceEvent.get_date(),
            time=maintenanceEvent.get_time(),
        )

        return render_template(
            'maintenanceEvent/maintenanceEventForm.jinja2',
            maintenanceEvent=eventModel,
            event_id=event_id,
            maintenance=maintenance,
        )

    @maintenanceEventInstances.route('/edit/<int:event_id>', methods=['POST'])
    @login_required
    @validate()
    def editPost(event_id: int, form: MaintenanceEventInstanceFormModel):
        maintenanceEvent = get_maintenance_event_by_id(event_id)

        if maintenanceEvent is None:
            abort(404)

        maintenance = get_maintenance_by_id(maintenanceEvent.maintenance_id)

        if maintenance is None:
            abort(404)

        maintenanceEvent.event_date = form.calculate_event_date()  # type: ignore[assignment]
        maintenanceEvent.maintenance_id = maintenance.id

        LOGGER.debug(f'Updated maintenance event: {maintenanceEvent}')
        db.session.commit()

        return redirect(url_for('maintenances.listMaintenances'))

    @maintenanceEventInstances.route('/delete/<int:event_id>')
    @login_required
    def delete(event_id: int):
        maintenanceEvent = get_maintenance_event_by_id(event_id)

        if maintenanceEvent is None:
            abort(404)

        LOGGER.debug(f'Deleted maintenance event: {maintenanceEvent}')
        db.session.delete(maintenanceEvent)
        db.session.commit()

        return redirect(url_for('maintenances.listMaintenances'))

    return maintenanceEventInstances
