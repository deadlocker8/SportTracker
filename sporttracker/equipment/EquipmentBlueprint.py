import logging

from flask import Blueprint, abort, redirect, render_template, url_for
from flask_login import current_user, login_required
from flask_pydantic import validate

from sporttracker import Constants
from sporttracker.equipment.EquipmentService import EquipmentFormModel, EquipmentModel, EquipmentService

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint(equipmentService: EquipmentService) -> Blueprint:
    equipment = Blueprint('equipment', __name__, static_folder='static', url_prefix='/equipment')

    @equipment.route('/', methods=['GET'])
    @login_required
    def listEquipment():
        return render_template(
            'equipment/equipment.jinja2', equipment=equipmentService.get_all_equipment(current_user.id)
        )

    @equipment.route('/add', methods=['GET'])
    @login_required
    def add():
        return render_template(
            'equipment/equipmentForm.jinja2',
        )

    @equipment.route('/post', methods=['POST'])
    @login_required
    @validate()
    def addPost(form: EquipmentFormModel):
        equipmentService.add_equipment(form, current_user.id)
        return redirect(url_for('equipment.equipment'))

    @equipment.route('/edit/<int:equipment_id>', methods=['GET'])
    @login_required
    def edit(equipment_id: int):
        equipmentItem = equipmentService.get_equipment_by_id(equipment_id, current_user.id)
        if equipment is None:
            abort(404)

        equipmentModel = EquipmentModel.create_from_equipment(equipmentItem)  # type: ignore[arg-type]

        return render_template('equipment/equipmentForm.jinja2', equipmentModel=equipmentModel)

    @equipment.route('/edit/<int:equipment_id>', methods=['POST'])
    @login_required
    @validate()
    def editPost(equipment_id: int, form: EquipmentFormModel):
        try:
            equipmentService.update_equipment(equipment_id, form, current_user.id)
            return redirect(url_for('equipment.equipment'))
        except ValueError:
            abort(404)

    @equipment.route('/delete/<int:equipment_id>', methods=['GET'])
    @login_required
    def delete(equipment_id: int):
        try:
            equipmentService.delete_equipment(equipment_id, current_user.id)
            return redirect(url_for('longDistanceTours.listLongDistanceTours'))
        except ValueError:
            abort(404)

    return equipment
