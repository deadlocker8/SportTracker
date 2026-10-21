import logging
from gettext import gettext

from flask import Blueprint, abort, redirect, render_template, url_for
from flask_login import current_user, login_required

from sporttracker import Constants
from sporttracker.equipment.bike.BikeEntity import Bike
from sporttracker.equipment.bike.BikeService import BikeService
from sporttracker.equipment.clothes.ClothesEntity import Clothes
from sporttracker.equipment.clothes.ClothesService import ClothesService
from sporttracker.equipment.custom.CustomEquipmentEntity import CustomEquipment
from sporttracker.equipment.custom.CustomEquipmentService import CustomEquipmentService
from sporttracker.equipment.EquipmentModel import EquipmentGroupModel
from sporttracker.equipment.EquipmentService import EquipmentService
from sporttracker.workout.WorkoutType import WorkoutType

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint(
    clothesService: ClothesService, bikeService: BikeService, customEquipmentService: CustomEquipmentService
) -> Blueprint:
    equipment = Blueprint('equipment', __name__, static_folder='static', url_prefix='/equipment')

    @equipment.route('/', methods=['GET'])
    @login_required
    def listEquipment():
        equipmentGroupsByWorkoutType: dict[WorkoutType, list[EquipmentGroupModel]] = {}

        bikes = bikeService.get_all_by_workout_type(WorkoutType.BIKING, current_user.id)
        bikingClothes = clothesService.get_all_by_workout_type(WorkoutType.BIKING, current_user.id)
        bikingCustom = customEquipmentService.get_all_by_workout_type(WorkoutType.BIKING, current_user.id)
        equipmentGroupsByWorkoutType[WorkoutType.BIKING] = [
            EquipmentGroupModel(
                name=gettext('Bikes'),
                icon=Bike.get_icon()[0],
                is_font_awesome_icon=Bike.get_icon()[1],
                add_url=url_for('equipment_bike.add', workout_type=WorkoutType.BIKING.name),
                items=bikes,
            ),
            EquipmentGroupModel(
                name=gettext('Clothes'),
                icon=Clothes.get_icon()[0],
                is_font_awesome_icon=Clothes.get_icon()[1],
                add_url=url_for('equipment_clothes.add', workout_type=WorkoutType.BIKING.name),
                items=bikingClothes,
            ),
            EquipmentGroupModel(
                name=gettext('Custom'),
                icon=CustomEquipment.get_icon()[0],
                is_font_awesome_icon=Clothes.get_icon()[1],
                add_url=url_for('equipment_custom.add', workout_type=WorkoutType.BIKING.name),
                items=bikingCustom,
            ),
        ]

        runningClothes = clothesService.get_all_by_workout_type(WorkoutType.RUNNING, current_user.id)
        runningCustom = customEquipmentService.get_all_by_workout_type(WorkoutType.RUNNING, current_user.id)
        equipmentGroupsByWorkoutType[WorkoutType.RUNNING] = [
            EquipmentGroupModel(
                name=gettext('Clothes'),
                icon=Clothes.get_icon()[0],
                is_font_awesome_icon=Clothes.get_icon()[1],
                add_url=url_for('equipment_clothes.add', workout_type=WorkoutType.RUNNING.name),
                items=runningClothes,
            ),
            EquipmentGroupModel(
                name=gettext('Custom'),
                icon=CustomEquipment.get_icon()[0],
                is_font_awesome_icon=Clothes.get_icon()[1],
                add_url=url_for('equipment_custom.add', workout_type=WorkoutType.BIKING.name),
                items=runningCustom,
            ),
        ]

        hikingClothes = clothesService.get_all_by_workout_type(WorkoutType.HIKING, current_user.id)
        hikingCustom = customEquipmentService.get_all_by_workout_type(WorkoutType.HIKING, current_user.id)
        equipmentGroupsByWorkoutType[WorkoutType.HIKING] = [
            EquipmentGroupModel(
                name=gettext('Clothes'),
                icon=Clothes.get_icon()[0],
                is_font_awesome_icon=Clothes.get_icon()[1],
                add_url=url_for('equipment_clothes.add', workout_type=WorkoutType.HIKING.name),
                items=hikingClothes,
            ),
            EquipmentGroupModel(
                name=gettext('Custom'),
                icon=CustomEquipment.get_icon()[0],
                is_font_awesome_icon=Clothes.get_icon()[1],
                add_url=url_for('equipment_custom.add', workout_type=WorkoutType.BIKING.name),
                items=hikingCustom,
            ),
        ]

        fitnessClothes = clothesService.get_all_by_workout_type(WorkoutType.FITNESS, current_user.id)
        fitnessCustom = customEquipmentService.get_all_by_workout_type(WorkoutType.HIKING, current_user.id)
        equipmentGroupsByWorkoutType[WorkoutType.FITNESS] = [
            EquipmentGroupModel(
                name=gettext('Clothes'),
                icon=Clothes.get_icon()[0],
                is_font_awesome_icon=Clothes.get_icon()[1],
                add_url=url_for('equipment_clothes.add', workout_type=WorkoutType.FITNESS.name),
                items=fitnessClothes,
            ),
            EquipmentGroupModel(
                name=gettext('Custom'),
                icon=CustomEquipment.get_icon()[0],
                is_font_awesome_icon=Clothes.get_icon()[1],
                add_url=url_for('equipment_custom.add', workout_type=WorkoutType.BIKING.name),
                items=fitnessCustom,
            ),
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
        elif isinstance(equipmentItem, Bike):
            return redirect(url_for('equipment_bike.edit', equipment_id=equipment_id))

        LOGGER.error(f'Could not determine edit url for equipment with id: {equipment_id}')
        abort(404)

    @equipment.route('/delete/<int:equipment_id>', methods=['GET'])
    @login_required
    def delete(equipment_id: int):
        equipmentItem = EquipmentService.get_equipment_by_id(equipment_id, current_user.id)
        if equipmentItem is None:
            abort(404)

        if isinstance(equipmentItem, Clothes):
            return redirect(url_for('equipment_clothes.delete', equipment_id=equipment_id))
        elif isinstance(equipmentItem, Bike):
            return redirect(url_for('equipment_bike.delete', equipment_id=equipment_id))

        LOGGER.error(f'Could not determine delete url for equipment with id: {equipment_id}')
        abort(404)

    return equipment
