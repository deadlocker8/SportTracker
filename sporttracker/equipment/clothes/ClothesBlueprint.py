import logging

from flask import Blueprint, abort, redirect, render_template, url_for
from flask_login import current_user, login_required
from flask_pydantic import validate

from sporttracker import Constants
from sporttracker.equipment.clothes.ClothesEntity import Clothes
from sporttracker.equipment.clothes.ClothesModel import ClothesFormModel, ClothesModel
from sporttracker.equipment.clothes.ClothesService import ClothesService
from sporttracker.workout.WorkoutType import WorkoutType

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint(clothesService: ClothesService) -> Blueprint:
    equipment_clothes = Blueprint(
        'equipment_clothes', __name__, static_folder='static', url_prefix='/equipment/clothes'
    )

    @equipment_clothes.route('/add/<string:workout_type>', methods=['GET'])
    @login_required
    def add(workout_type: str):
        return render_template(
            'equipment/clothes/clothesForm.jinja2',
            workout_type=WorkoutType(workout_type),  # type: ignore[call-arg]
            icon=Clothes.get_icon()[0],
            is_font_awesome_icon=Clothes.get_icon()[1],
        )

    @equipment_clothes.route('/post', methods=['POST'])
    @login_required
    @validate()
    def addPost(form: ClothesFormModel):
        clothesService.add_clothes(form, current_user.id)
        return redirect(url_for('equipment.listEquipment'))

    @equipment_clothes.route('/edit/<int:equipment_id>', methods=['GET'])
    @login_required
    def edit(equipment_id: int):
        equipmentItem = clothesService.get_clothes_by_id(equipment_id, current_user.id)
        if equipmentItem is None:
            abort(404)

        equipment = ClothesModel(
            id=equipmentItem.id,
            workout_type=equipmentItem.workout_type,
            name=equipmentItem.name,
            purchase_date=equipmentItem.purchase_date,
            is_active=equipmentItem.is_active,
            inactive_date=equipmentItem.inactive_date,
            clothes_type=equipmentItem.clothes_type,
        )

        return render_template(
            'equipment/clothes/clothesForm.jinja2',
            equipment=equipment,
            workout_type=equipmentItem.workout_type,
            icon=Clothes.get_icon()[0],
            is_font_awesome_icon=Clothes.get_icon()[1],
        )

    @equipment_clothes.route('/edit/<int:equipment_id>', methods=['POST'])
    @login_required
    @validate()
    def editPost(equipment_id: int, form: ClothesFormModel):
        try:
            clothesService.update_clothes(equipment_id, form, current_user.id)
            return redirect(url_for('equipment.listEquipment'))
        except ValueError:
            abort(404)

    @equipment_clothes.route('/delete/<int:equipment_id>', methods=['GET'])
    @login_required
    def delete(equipment_id: int):
        try:
            clothesService.delete_clothes(equipment_id, current_user.id)
            return redirect(url_for('equipment.listEquipment'))
        except ValueError:
            abort(404)

    return equipment_clothes
