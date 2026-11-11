import logging

from flask import Blueprint, abort, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from flask_pydantic import validate

from sporttracker import Constants
from sporttracker.equipment.EquipmentService import EquipmentService
from sporttracker.equipment.presets.EquipmentPresetModel import EquipmentPresetFormModel
from sporttracker.equipment.presets.EquipmentPresetService import EquipmentPresetService
from sporttracker.workout.WorkoutType import WorkoutType

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint() -> Blueprint:
    equipmentPresets = Blueprint('equipment_presets', __name__, static_folder='static', url_prefix='/equipment/presets')

    @equipmentPresets.route('/list/<string:workout_type>', methods=['GET'])
    @login_required
    def listPresets(workout_type: str):
        try:
            workoutType = WorkoutType(workout_type)  # type: ignore[call-arg]
        except ValueError:
            abort(404)

        presets = EquipmentPresetService.get_all_by_workout_type(workoutType, current_user.id)

        return render_template(
            'equipment/equipmentPresets.jinja2',
            workout_type=workoutType,
            presets=presets,
        )

    @equipmentPresets.route('/add/<string:workout_type>', methods=['GET'])
    @login_required
    def add(workout_type: str):
        try:
            workoutType = WorkoutType(workout_type)  # type: ignore[call-arg]
        except ValueError:
            abort(404)

        return render_template(
            'equipment/equipmentPresetForm.jinja2',
            workout_type=workoutType,
            preset=None,
            equipment_groups=EquipmentService.get_selection_groups_by_workout_type(workoutType, current_user.id),
        )

    @equipmentPresets.route('/post', methods=['POST'])
    @login_required
    @validate()
    def addPost(form: EquipmentPresetFormModel):
        try:
            workoutType = WorkoutType(form.workout_type)  # type: ignore[call-arg]
        except ValueError:
            abort(404)

        equipmentIds = [int(item) for item in request.form.getlist('equipment_ids')]
        EquipmentPresetService.add(form.name, workoutType, equipmentIds, current_user.id)

        return redirect(url_for('equipment_presets.listPresets', workout_type=workoutType.name))

    @equipmentPresets.route('/edit/<int:preset_id>', methods=['GET'])
    @login_required
    def edit(preset_id: int):
        preset = EquipmentPresetService.get_by_id(preset_id, current_user.id)
        if preset is None:
            abort(404)

        return render_template(
            'equipment/equipmentPresetForm.jinja2',
            workout_type=preset.workout_type,
            preset=preset,
            equipment_groups=EquipmentService.get_selection_groups_by_workout_type(
                preset.workout_type, current_user.id
            ),
        )

    @equipmentPresets.route('/edit/<int:preset_id>', methods=['POST'])
    @login_required
    @validate()
    def editPost(preset_id: int, form: EquipmentPresetFormModel):
        preset = EquipmentPresetService.get_by_id(preset_id, current_user.id)
        if preset is None:
            abort(404)

        equipmentIds = [int(item) for item in request.form.getlist('equipment_ids')]

        try:
            EquipmentPresetService.edit(preset_id, form.name, equipmentIds, current_user.id)
        except ValueError:
            abort(404)

        return redirect(url_for('equipment_presets.listPresets', workout_type=preset.workout_type.name))

    @equipmentPresets.route('/delete/<int:preset_id>', methods=['GET'])
    @login_required
    def delete(preset_id: int):
        preset = EquipmentPresetService.get_by_id(preset_id, current_user.id)
        if preset is None:
            abort(404)

        try:
            EquipmentPresetService.delete(preset_id, current_user.id)
        except ValueError:
            abort(404)

        return redirect(url_for('equipment_presets.listPresets', workout_type=preset.workout_type.name))

    return equipmentPresets
