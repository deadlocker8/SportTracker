import logging
from dataclasses import dataclass
from typing import Any

from flask import Blueprint, abort, redirect, render_template, request, url_for
from flask_babel import gettext
from flask_login import current_user, login_required
from flask_pydantic import validate
from pydantic import BaseModel, field_validator

from sporttracker import Constants
from sporttracker.db import db
from sporttracker.equipment.EquipmentService import EquipmentService
from sporttracker.maintenance.MaintenanceEntity import Maintenance, get_maintenance_by_id
from sporttracker.maintenance.MaintenanceEventInstanceEntity import (
    get_maintenance_events_by_maintenance_id,
)
from sporttracker.maintenance.MaintenanceEventsCollector import create_maintenance_model, get_maintenances_with_events
from sporttracker.maintenance.MaintenanceFilterStateEntity import get_maintenance_filter_state_by_user
from sporttracker.quickFilter.QuickFilterStateEntity import get_quick_filter_state_by_user
from sporttracker.user.CustomWorkoutFieldEntity import get_custom_fields_grouped_by_distance_workout_types_with_values
from sporttracker.workout.WorkoutType import WorkoutType

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
    equipment_id: int | None = None


class MaintenanceFormModel(BaseModel):
    type: str
    description: str
    is_reminder_active: bool | None = None
    reminder_limit: int | None = None
    custom_field_id: int | None = None
    custom_field_value: str | None = None
    equipment_id: int | None = None

    @field_validator('description', mode='before')
    @classmethod
    def description_strip(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator(*['custom_field_id', 'equipment_id'], mode='before')
    def nullable_id_check(cls, value: str, info) -> str | None:
        if isinstance(value, str):
            value = value.strip()

        if value == '':
            return None

        return value


def _get_valid_equipment_id(
    equipment_id: int | None,
    workout_type: WorkoutType,
    user_id: int,
    existing_equipment_id: int | None = None,
) -> int | None:
    if equipment_id is None:
        return None

    equipment = EquipmentService.get_equipment_by_id(equipment_id, user_id)
    if equipment is None:
        return None

    if equipment.workout_type != workout_type:
        return None

    if not equipment.is_active and equipment.id != existing_equipment_id:
        return None

    return equipment.id


def construct_blueprint():
    maintenances = Blueprint('maintenances', __name__, static_folder='static', url_prefix='/maintenances')

    @maintenances.route('/', methods=['GET'])
    @login_required
    def listMaintenances():
        quickFilterState = get_quick_filter_state_by_user(current_user.id)
        maintenanceFilterState = get_maintenance_filter_state_by_user(current_user.id)

        maintenancesWithEvents = get_maintenances_with_events(quickFilterState, maintenanceFilterState, current_user.id)

        customFieldsByWorkoutType = get_custom_fields_grouped_by_distance_workout_types_with_values(
            quickFilterState.get_active_distance_workout_types()
        )

        hasCustomWorkoutFields = any(len(fields) > 0 for fields in customFieldsByWorkoutType.values())

        return render_template(
            'maintenance/maintenances.jinja2',
            maintenancesWithEvents=maintenancesWithEvents,
            quickFilterState=quickFilterState,
            customFieldsByWorkoutType=customFieldsByWorkoutType,
            hasCustomWorkoutFields=hasCustomWorkoutFields,
            maintenanceFilterState=maintenanceFilterState,
        )

    @maintenances.route('/<int:maintenance_id>')
    @login_required
    def showSingleMaintenance(maintenance_id: int):
        maintenance = get_maintenance_by_id(maintenance_id)

        if maintenance is None:
            return render_template('map/mapNotFound.jinja2', errorText=gettext('Maintenance does not exist anymore'))

        return render_template(
            'maintenance/maintenance.jinja2',
            maintenanceWithEvents=create_maintenance_model(maintenance),
        )

    @maintenances.route('/add', methods=['GET'])
    @login_required
    def add():
        return render_template(
            'maintenance/maintenanceForm.jinja2',
            customFieldsByWorkoutType=get_custom_fields_grouped_by_distance_workout_types_with_values(
                WorkoutType.get_distance_workout_types()
            ),
            equipmentByWorkoutType=EquipmentService.get_equipment_grouped_by_workout_type_and_type(
                WorkoutType.get_distance_workout_types(), current_user.id
            ),
            maintenanceFilterState=get_maintenance_filter_state_by_user(current_user.id),
        )

    @maintenances.route('/post', methods=['POST'])
    @login_required
    @validate()
    def addPost(form: MaintenanceFormModel):
        reminderLimit = None
        if form.reminder_limit is not None:
            reminderLimit = form.reminder_limit * 1000

        workoutType = WorkoutType(form.type)  # type: ignore[call-arg]
        if workoutType in WorkoutType.get_distance_workout_types():
            customFieldId = form.custom_field_id
            customFieldValue = form.custom_field_value
            if customFieldValue is None:
                # if no value is selected then no custom field id should be saved
                customFieldId = None
            if customFieldId is None:
                # if no custom field is selected then the value needs to be ignored
                customFieldValue = None

            equipmentId = _get_valid_equipment_id(form.equipment_id, workoutType, current_user.id)
            if equipmentId is not None:
                customFieldId = None
                customFieldValue = None
            elif customFieldId is not None:
                equipmentId = None

            maintenance = Maintenance(
                type=workoutType,
                description=form.description,
                user_id=current_user.id,
                is_reminder_active=bool(form.is_reminder_active),
                reminder_limit=reminderLimit,
                custom_workout_field_id=customFieldId,
                custom_workout_field_value=customFieldValue,
                equipment_id=equipmentId,
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

    @maintenances.route('/edit/<int:maintenance_id>', methods=['GET'])
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
            equipment_id=maintenance.equipment_id,
        )

        return render_template(
            'maintenance/maintenanceForm.jinja2',
            maintenance=model,
            maintenance_id=maintenance_id,
            customFieldsByWorkoutType=get_custom_fields_grouped_by_distance_workout_types_with_values(
                WorkoutType.get_distance_workout_types()
            ),
            equipmentByWorkoutType=EquipmentService.get_equipment_grouped_by_workout_type_and_type(
                WorkoutType.get_distance_workout_types(), current_user.id, maintenance.equipment_id
            ),
            maintenanceFilterState=get_maintenance_filter_state_by_user(current_user.id),
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

            customFieldId = form.custom_field_id
            customFieldValue = form.custom_field_value
            if customFieldValue is None:
                # if no value is selected then no custom field id should be saved
                customFieldId = None
            if customFieldId is None:
                # if no custom field is selected then the value needs to be ignored
                customFieldValue = None

            equipmentId = _get_valid_equipment_id(
                form.equipment_id, workoutType, current_user.id, maintenance.equipment_id
            )
            if equipmentId is not None:
                customFieldId = None
                customFieldValue = None
            elif customFieldId is not None:
                equipmentId = None

            maintenance.custom_workout_field_id = customFieldId
            maintenance.custom_workout_field_value = customFieldValue  # type: ignore[assignment]
            maintenance.equipment_id = equipmentId

        else:
            maintenance.is_reminder_active = False
            maintenance.reminder_limit = None  # type: ignore[assignment]
            maintenance.custom_workout_field_id = None
            maintenance.custom_workout_field_value = None
            maintenance.equipment_id = None

        LOGGER.debug(f'Updated maintenance: {maintenance}')
        db.session.commit()

        return redirect(url_for('maintenances.listMaintenances'))

    @maintenances.route('/delete/<int:maintenance_id>', methods=['GET'])
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

        maintenanceFilterState = get_maintenance_filter_state_by_user(current_user.id)
        maintenanceFilterState.custom_workout_field_id = customWorkoutFieldId
        maintenanceFilterState.custom_workout_field_value = customWorkoutFieldValue  # type: ignore[assignment]
        db.session.commit()

        return redirect(url_for('maintenances.listMaintenances'))

    @maintenances.route('/resetFilter', methods=['GET'])
    @login_required
    def resetFilter():
        maintenanceFilterState = get_maintenance_filter_state_by_user(current_user.id)
        maintenanceFilterState.reset()
        db.session.commit()

        return redirect(url_for('maintenances.listMaintenances'))

    return maintenances
