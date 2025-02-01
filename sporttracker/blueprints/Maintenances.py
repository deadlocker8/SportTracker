import logging
from dataclasses import dataclass

from flask import Blueprint, render_template, redirect, url_for, abort
from flask_login import login_required, current_user
from flask_pydantic import validate
from pydantic import BaseModel

from sporttracker.logic import Constants
from sporttracker.logic.MaintenanceEventsCollector import get_maintenances_with_events
from sporttracker.logic.QuickFilterState import (
    get_quick_filter_state_from_session,
)
from sporttracker.logic.model.Maintenance import Maintenance, get_maintenance_by_id
from sporttracker.logic.model.MaintenanceEventInstance import (
    get_maintenance_events_by_maintenance_id,
)
from sporttracker.logic.model.WorkoutType import WorkoutType
from sporttracker.logic.model.db import db

LOGGER = logging.getLogger(Constants.APP_NAME)


@dataclass
class MaintenanceModel:
    id: int | None
    type: WorkoutType
    description: str
    is_reminder_active: bool
    reminder_limit: int | None


class MaintenanceFormModel(BaseModel):
    type: str
    description: str
    is_reminder_active: bool | None = None
    reminder_limit: int | None = None


def construct_blueprint():
    maintenances = Blueprint(
        'maintenances', __name__, static_folder='static', url_prefix='/maintenances'
    )

    @maintenances.route('/')
    @login_required
    def listMaintenances():
        quickFilterState = get_quick_filter_state_from_session()

        maintenancesWithEvents = get_maintenances_with_events(quickFilterState)

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
        reminderLimit = None
        if form.reminder_limit is not None:
            reminderLimit = form.reminder_limit * 1000

        workoutType = WorkoutType(form.type)  # type: ignore[call-arg]
        if workoutType in WorkoutType.get_distance_workout_types():
            maintenance = Maintenance(
                type=workoutType,
                description=form.description,
                user_id=current_user.id,
                is_reminder_active=bool(form.is_reminder_active),
                reminder_limit=reminderLimit,
            )
        else:
            maintenance = Maintenance(
                type=workoutType,
                description=form.description,
                user_id=current_user.id,
                is_reminder_active=False,
                reminder_limit=None,
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
            is_reminder_active=maintenance.is_reminder_active,  # type: ignore[arg-type]
            reminder_limit=None
            if maintenance.reminder_limit is None
            else maintenance.reminder_limit // 1000,  # type: ignore[arg-type]
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

        reminderLimit = None
        if form.reminder_limit is not None:
            reminderLimit = form.reminder_limit * 1000

        workoutType = WorkoutType(form.type)  # type: ignore[call-arg]
        maintenance.type = workoutType
        maintenance.description = form.description  # type: ignore[assignment]
        maintenance.user_id = current_user.id

        if workoutType in WorkoutType.get_distance_workout_types():
            maintenance.is_reminder_active = bool(form.is_reminder_active)
            maintenance.reminder_limit = reminderLimit  # type: ignore[assignment]
        else:
            maintenance.is_reminder_active = False
            maintenance.reminder_limit = None  # type: ignore[assignment]

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
