import logging

from flask import Blueprint, abort, redirect, render_template, url_for
from flask_login import current_user, login_required
from flask_pydantic import validate

from sporttracker import Constants
from sporttracker.equipment.custom.CustomEquipmentEntity import CustomEquipment
from sporttracker.equipment.custom.CustomEquipmentModel import CustomEquipmentFormModel, CustomEquipmentModel
from sporttracker.equipment.custom.CustomEquipmentService import CustomEquipmentService
from sporttracker.workout.WorkoutType import WorkoutType

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint(customEquipmentService: CustomEquipmentService) -> Blueprint:
    equipment_custom = Blueprint('equipment_custom', __name__, static_folder='static', url_prefix='/equipment/custom')

    @equipment_custom.route('/add/<string:workout_type>', methods=['GET'])
    @login_required
    def add(workout_type: str):
        return render_template(
            'equipment/custom/customEquipmentForm.jinja2',
            workout_type=WorkoutType(workout_type),  # type: ignore[call-arg]
            icon=CustomEquipment.get_icon()[0],
            is_font_awesome_icon=CustomEquipment.get_icon()[1],
        )

    @equipment_custom.route('/post', methods=['POST'])
    @login_required
    @validate()
    def addPost(form: CustomEquipmentFormModel):
        customEquipmentService.add(form, current_user.id)
        return redirect(url_for('equipment.listEquipment'))

    @equipment_custom.route('/edit/<int:equipment_id>', methods=['GET'])
    @login_required
    def edit(equipment_id: int):
        equipmentItem = customEquipmentService.get_by_id(equipment_id, current_user.id)
        if equipmentItem is None:
            abort(404)

        equipment = CustomEquipmentModel(
            id=equipmentItem.id,
            workout_type=equipmentItem.workout_type,
            name=equipmentItem.name,
            is_owned=equipmentItem.is_owned,
            purchase_date=equipmentItem.purchase_date,
            is_active=equipmentItem.is_active,
            inactive_date=equipmentItem.inactive_date,
        )

        return render_template(
            'equipment/custom/customEquipmentForm.jinja2',
            equipment=equipment,
            workout_type=equipmentItem.workout_type,
            icon=CustomEquipment.get_icon()[0],
            is_font_awesome_icon=CustomEquipment.get_icon()[1],
        )

    @equipment_custom.route('/edit/<int:equipment_id>', methods=['POST'])
    @login_required
    @validate()
    def editPost(equipment_id: int, form: CustomEquipmentFormModel):
        try:
            customEquipmentService.edit(equipment_id, form, current_user.id)
            return redirect(url_for('equipment.listEquipment'))
        except ValueError:
            abort(404)

    @equipment_custom.route('/delete/<int:equipment_id>', methods=['GET'])
    @login_required
    def delete(equipment_id: int):
        try:
            customEquipmentService.delete(equipment_id, current_user.id)
            return redirect(url_for('equipment.listEquipment'))
        except ValueError:
            abort(404)

    return equipment_custom
