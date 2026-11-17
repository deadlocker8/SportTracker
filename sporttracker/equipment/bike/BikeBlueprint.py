import logging

from flask import Blueprint, abort, redirect, render_template, url_for
from flask_login import current_user, login_required
from flask_pydantic import validate

from sporttracker import Constants
from sporttracker.equipment.bike.BikeEntity import Bike
from sporttracker.equipment.bike.BikeModel import BikeFormModel, BikeModel
from sporttracker.equipment.bike.BikeService import BikeService
from sporttracker.workout.WorkoutType import WorkoutType

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint(bikeService: BikeService) -> Blueprint:
    equipment_bike = Blueprint('equipment_bike', __name__, static_folder='static', url_prefix='/equipment/bike')

    @equipment_bike.route('/add/<string:workout_type>', methods=['GET'])
    @login_required
    def add(workout_type: str):
        return render_template(
            'equipment/bike/bikeForm.jinja2',
            workout_type=WorkoutType(workout_type),  # type: ignore[call-arg]
            icon=Bike.get_icon()[0],
            is_font_awesome_icon=Bike.get_icon()[1],
        )

    @equipment_bike.route('/post', methods=['POST'])
    @login_required
    @validate()
    def addPost(form: BikeFormModel):
        bikeService.add(form, current_user.id)
        return redirect(url_for('equipment.listEquipment'))

    @equipment_bike.route('/edit/<int:equipment_id>', methods=['GET'])
    @login_required
    def edit(equipment_id: int):
        equipmentItem = bikeService.get_by_id(equipment_id, current_user.id)
        if equipmentItem is None:
            abort(404)

        equipment = BikeModel(
            id=equipmentItem.id,
            workout_type=equipmentItem.workout_type,
            name=equipmentItem.name,
            is_owned=equipmentItem.is_owned,
            purchase_date=equipmentItem.purchase_date,
            is_active=equipmentItem.is_active,
            inactive_date=equipmentItem.inactive_date,
        )

        return render_template(
            'equipment/bike/bikeForm.jinja2',
            equipment=equipment,
            workout_type=equipmentItem.workout_type,
            icon=Bike.get_icon()[0],
            is_font_awesome_icon=Bike.get_icon()[1],
        )

    @equipment_bike.route('/edit/<int:equipment_id>', methods=['POST'])
    @login_required
    @validate()
    def editPost(equipment_id: int, form: BikeFormModel):
        try:
            bikeService.edit(equipment_id, form, current_user.id)
            return redirect(url_for('equipment.listEquipment'))
        except ValueError:
            abort(404)

    @equipment_bike.route('/delete/<int:equipment_id>', methods=['GET'])
    @login_required
    def delete(equipment_id: int):
        try:
            bikeService.delete(equipment_id, current_user.id)
            return redirect(url_for('equipment.listEquipment'))
        except ValueError:
            abort(404)

    return equipment_bike
