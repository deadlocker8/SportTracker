import logging
from gettext import gettext

from flask import Blueprint, render_template
from flask_login import current_user, login_required

from sporttracker import Constants
from sporttracker.equipment.clothes.ClothesService import ClothesService
from sporttracker.equipment.EquipmentModel import EquipmentGroupModel
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

        equipmentGroupsByWorkoutType[WorkoutType.RUNNING] = [
            EquipmentGroupModel(name=gettext('Clothes'), icon='apparel', is_font_awesome_icon=False, items=[])
        ]

        equipmentGroupsByWorkoutType[WorkoutType.HIKING] = [
            EquipmentGroupModel(name=gettext('Clothes'), icon='apparel', is_font_awesome_icon=False, items=[])
        ]

        equipmentGroupsByWorkoutType[WorkoutType.FITNESS] = [
            EquipmentGroupModel(name=gettext('Clothes'), icon='apparel', is_font_awesome_icon=False, items=[])
        ]

        return render_template('equipment/equipment.jinja2', equipmentGroupsByWorkoutType=equipmentGroupsByWorkoutType)

    return equipment
