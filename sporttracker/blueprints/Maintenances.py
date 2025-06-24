import logging
from dataclasses import dataclass

from flask import Blueprint, render_template, redirect, url_for, abort, session, request
from flask_login import login_required, current_user
from flask_pydantic import validate
from pydantic import BaseModel

from sporttracker.logic import Constants
from sporttracker.logic.MaintenanceEventsCollector import get_maintenances_with_events
from sporttracker.logic.MaintenanceFilterState import MaintenanceFilterState, get_maintenances_filter_state_from_session
from sporttracker.logic.QuickFilterState import (
    get_quick_filter_state_from_session,
)
from sporttracker.logic.model.CustomWorkoutField import get_custom_fields_grouped_by_distance_workout_types_with_values
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
    custom_field_id: int | None = None
    custom_field_value: str | None = None


class MaintenanceFormModel(BaseModel):
    type: str
    description: str
    is_reminder_active: bool | None = None
    reminder_limit: int | None = None
    custom_field_id: int | None = None
    custom_field_value: str | None = None


def construct_blueprint():
    maintenances = Blueprint('maintenances', __name__, static_folder='static', url_prefix='/maintenances')

    @maintenances.route('/')
    @login_required
    def listMaintenances():
        quickFilterState = get_quick_filter_state_from_session()
        maintenanceFilterState = get_maintenances_filter_state_from_session()

        maintenancesWithEvents = get_maintenances_with_events(quickFilterState, maintenanceFilterState, current_user.id)

        customFieldsByWorkoutType = get_custom_fields_grouped_by_distance_workout_types_with_values(
            quickFilterState.get_active_distance_workout_types()
        )

        hasCustomWorkoutFields = any([len(fields) > 0 for fields in customFieldsByWorkoutType.values()])

        return render_template(
            'maintenances/maintenances.jinja2',
            maintenancesWithEvents=maintenancesWithEvents,
            quickFilterState=quickFilterState,
            customFieldsByWorkoutType=customFieldsByWorkoutType,
            hasCustomWorkoutFields=hasCustomWorkoutFields,
            maintenanceFilterState=maintenanceFilterState,
        )

    @maintenances.route('/add')
    @login_required
    def add():
        return render_template(
            'maintenances/maintenanceForm.jinja2',
            customFieldsByWorkoutType=get_custom_fields_grouped_by_distance_workout_types_with_values(
                WorkoutType.get_distance_workout_types()
            ),
            maintenanceFilterState=get_maintenances_filter_state_from_session(),
        )

    @maintenances.route('/post', methods=['POST'])
    @login_required
    @validate()
    def addPost(form: MaintenanceFormModel):
        reminderLimit = None
        if form.reminder_limit is not None:
            reminderLimit = form.reminder_limit * 1000

        customFieldId = form.custom_field_id
        if form.custom_field_value is None:
            # if no value is selected then no custom field id should be saved
            customFieldId = None

        customFieldValue = form.custom_field_value
        if form.custom_field_id is None:
            # if no custom field is selected then the value needs to be ignored
            customFieldValue = None

        workoutType = WorkoutType(form.type)  # type: ignore[call-arg]
        if workoutType in WorkoutType.get_distance_workout_types():
            maintenance = Maintenance(
                type=workoutType,
                description=form.description,
                user_id=current_user.id,
                is_reminder_active=bool(form.is_reminder_active),
                reminder_limit=reminderLimit,
                custom_workout_field_id=customFieldId,
                custom_workout_field_value=customFieldValue,
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
            reminder_limit=None if maintenance.reminder_limit is None else maintenance.reminder_limit // 1000,
            # type: ignore[arg-type]
            custom_field_id=maintenance.custom_workout_field_id,
            custom_field_value=maintenance.custom_workout_field_value,  # type: ignore[arg-type]
        )

        return render_template(
            'maintenances/maintenanceForm.jinja2',
            maintenance=model,
            maintenance_id=maintenance_id,
            customFieldsByWorkoutType=get_custom_fields_grouped_by_distance_workout_types_with_values(
                WorkoutType.get_distance_workout_types()
            ),
            maintenanceFilterState=get_maintenances_filter_state_from_session(),
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

            maintenance.custom_workout_field_id = form.custom_field_id
            if form.custom_field_value is None:
                # if no value is selected then no custom field id should be saved
                maintenance.custom_workout_field_id = None

            maintenance.custom_workout_field_value = form.custom_field_value  # type: ignore[assignment]
            if form.custom_field_id is None:
                # if no custom field is selected then the value needs to be ignored
                maintenance.custom_workout_field_value = None  # type: ignore[assignment]

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

        events = get_maintenance_events_by_maintenance_id(maintenance_id, current_user.id)
        for event in events:
            LOGGER.debug(f'Deleted maintenance event: {event}')
            db.session.delete(event)

        db.session.commit()

        LOGGER.debug(f'Deleted maintenance: {maintenance} and {len(events)} events')
        db.session.delete(maintenance)
        db.session.commit()

        return redirect(url_for('maintenances.listMaintenances'))

    @maintenances.route('/applyFilter', methods=['POST'])
    @login_required
    def applyFilter():
        customWorkoutFieldId: str | int | None = request.form.get('customWorkoutFieldId', None)
        customWorkoutFieldValue = request.form.get('customWorkoutFieldValue', None)
        if customWorkoutFieldId is None and customWorkoutFieldValue is None:
            return redirect(url_for('maintenances.resetFilter'))

        if customWorkoutFieldId == '':
            customWorkoutFieldId = None

        if customWorkoutFieldId is not None:
            customWorkoutFieldId = int(customWorkoutFieldId)

        maintenanceFilterState = get_maintenances_filter_state_from_session()
        maintenanceFilterState.update(customWorkoutFieldId, customWorkoutFieldValue)
        session[MaintenanceFilterState.SESSION_ATTRIBUTE_NAME] = maintenanceFilterState.to_json()

        return redirect(url_for('maintenances.listMaintenances'))

    @maintenances.route('/resetFilter')
    @login_required
    def resetFilter():
        session[MaintenanceFilterState.SESSION_ATTRIBUTE_NAME] = MaintenanceFilterState().to_json()
        return redirect(url_for('maintenances.listMaintenances'))

    return maintenances
