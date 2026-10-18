import logging
from gettext import gettext

from flask import Blueprint, abort, redirect, render_template, url_for
from flask_login import current_user, login_required

from sporttracker import Constants
from sporttracker.equipment.clothes.ClothesEntity import Clothes
from sporttracker.equipment.clothes.ClothesService import ClothesService
from sporttracker.equipment.EquipmentModel import EquipmentGroupModel
from sporttracker.equipment.EquipmentService import EquipmentService
from sporttracker.workout.WorkoutType import WorkoutType

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint(clothesService: ClothesService) -> Blueprint:
    equipment = Blueprint('equipment', __name__, static_folder='static', url_prefix='/equipment')

    @equipment.route('/', methods=['GET'])
    @login_required
    def listEquipment():
        equipmentGroupsByWorkoutType: dict[WorkoutType, list[EquipmentGroupModel]] = {}

        bikingClothes = clothesService.get_all_clothes_by_workout_type(WorkoutType.BIKING, current_user.id)
        equipmentGroupsByWorkoutType[WorkoutType.BIKING] = [
            EquipmentGroupModel(name=gettext('Bikes'), icon='fa-bicycle', is_font_awesome_icon=True, items=[]),
            EquipmentGroupModel(
                name=gettext('Clothes'), icon='apparel', is_font_awesome_icon=False, items=bikingClothes
            ),
        ]

        runningClothes = clothesService.get_all_clothes_by_workout_type(WorkoutType.RUNNING, current_user.id)
        equipmentGroupsByWorkoutType[WorkoutType.RUNNING] = [
            EquipmentGroupModel(
                name=gettext('Clothes'), icon='apparel', is_font_awesome_icon=False, items=runningClothes
            )
        ]

        hikingClothes = clothesService.get_all_clothes_by_workout_type(WorkoutType.HIKING, current_user.id)
        equipmentGroupsByWorkoutType[WorkoutType.HIKING] = [
            EquipmentGroupModel(
                name=gettext('Clothes'), icon='apparel', is_font_awesome_icon=False, items=hikingClothes
            )
        ]

        fitnessClothes = clothesService.get_all_clothes_by_workout_type(WorkoutType.FITNESS, current_user.id)
        equipmentGroupsByWorkoutType[WorkoutType.FITNESS] = [
            EquipmentGroupModel(
                name=gettext('Clothes'), icon='apparel', is_font_awesome_icon=False, items=fitnessClothes
            )
        ]

        return render_template('equipment/equipment.jinja2', equipmentGroupsByWorkoutType=equipmentGroupsByWorkoutType)

    @equipment.route('/edit/<int:equipment_id>', methods=['GET'])
    @login_required
    def edit(equipment_id: int):
        equipmentItem = EquipmentService.get_equipment_by_id(equipment_id, current_user.id)
        if equipmentItem is None:
            abort(404)

        if isinstance(equipmentItem, Clothes):
            return redirect(url_for('equipment_clothes.edit', equipment_id=equipment_id))

        abort(404)

    @equipment.route('/delete/<int:equipment_id>', methods=['GET'])
    @login_required
    def delete(equipment_id: int):
        equipmentItem = EquipmentService.get_equipment_by_id(equipment_id, current_user.id)
        if equipmentItem is None:
            abort(404)

        if isinstance(equipmentItem, Clothes):
            return redirect(url_for('equipment_clothes.delete', equipment_id=equipment_id))

        abort(404)

    return equipment
