import logging
from typing import cast

from flask import Blueprint, abort, redirect, render_template, request, url_for
from flask_babel import gettext
from flask_login import current_user, login_required

from sporttracker import Constants
from sporttracker.db import db
from sporttracker.equipment.bike.BikeEntity import Bike
from sporttracker.equipment.bike.BikeService import BikeService
from sporttracker.equipment.clothes.ClothesEntity import Clothes
from sporttracker.equipment.clothes.ClothesService import ClothesService
from sporttracker.equipment.clothes.ClothesType import ClothesType
from sporttracker.equipment.custom.CustomEquipmentEntity import CustomEquipment
from sporttracker.equipment.custom.CustomEquipmentService import CustomEquipmentService
from sporttracker.equipment.EquipmentFilterStateEntity import (
    EquipmentFilterState,
    get_equipment_filter_state_by_user,
)
from sporttracker.equipment.EquipmentModel import EquipmentGroupModel, EquipmentStatisticModel
from sporttracker.equipment.EquipmentService import EquipmentService
from sporttracker.equipment.EquipmentType import EquipmentType
from sporttracker.quickFilter.QuickFilterStateEntity import get_quick_filter_state_by_user
from sporttracker.workout.WorkoutType import WorkoutType

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint(
    clothesService: ClothesService, bikeService: BikeService, customEquipmentService: CustomEquipmentService
) -> Blueprint:
    equipment = Blueprint('equipment', __name__, static_folder='static', url_prefix='/equipment')

    @equipment.route('/', methods=['GET'])
    @login_required
    def listEquipment():
        equipmentFilterState = get_equipment_filter_state_by_user(current_user.id)
        quickFilterState = get_quick_filter_state_by_user(current_user.id)

        includeBikesByWorkoutType = {
            WorkoutType.BIKING: True,
            WorkoutType.RUNNING: False,
            WorkoutType.HIKING: False,
            WorkoutType.FITNESS: False,
        }
        activeWorkoutTypes = quickFilterState.get_active_workout_types()

        equipmentGroupsByWorkoutType: dict[WorkoutType, list[EquipmentGroupModel]] = {
            workoutType: __create_equipment_groups_for_workout_type(
                workoutType, current_user.id, includeBikes, equipmentFilterState
            )
            for workoutType, includeBikes in includeBikesByWorkoutType.items()
            if workoutType in activeWorkoutTypes
        }

        return render_template(
            'equipment/equipment.jinja2',
            equipmentGroupsByWorkoutType=equipmentGroupsByWorkoutType,
            equipmentFilterState=equipmentFilterState,
            quickFilterState=quickFilterState,
        )

    @equipment.route('/applyFilter', methods=['POST'])
    @login_required
    def applyFilter():
        selectedEquipmentTypes = [
            EquipmentType(value)  # type: ignore[call-arg]
            for key, value in request.form.items()
            if key.startswith('equipmentFilterEquipmentType')
        ]
        equipmentTypes = {t: t in selectedEquipmentTypes for t in EquipmentType}

        selectedClothesTypes = [
            ClothesType(value)  # type: ignore[call-arg]
            for key, value in request.form.items()
            if key.startswith('equipmentFilterClothesType')
        ]
        clothesTypes = {t: t in selectedClothesTypes for t in ClothesType}

        equipmentFilterState = get_equipment_filter_state_by_user(current_user.id)
        equipmentFilterState.update(
            equipmentTypes,
            clothesTypes,
            request.form.get('equipmentFilterStatusActive', 'off').strip().lower() == 'on',
            request.form.get('equipmentFilterStatusInactive', 'off').strip().lower() == 'on',
            request.form.get('equipmentFilterOwnedActive', 'off').strip().lower() == 'on',
            request.form.get('equipmentFilterNotOwnedInactive', 'off').strip().lower() == 'on',
        )
        db.session.commit()

        return redirect(request.form.get('redirectUrl', url_for('equipment.listEquipment')))

    @equipment.route('/resetFilter', methods=['GET'])
    @login_required
    def resetFilter():
        equipmentFilterState = get_equipment_filter_state_by_user(current_user.id)
        equipmentFilterState.reset()
        db.session.commit()
        return redirect(request.args.get('redirectUrl', url_for('equipment.listEquipment')))

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
        elif isinstance(equipmentItem, CustomEquipment):
            return redirect(url_for('equipment_custom.edit', equipment_id=equipment_id))

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
        elif isinstance(equipmentItem, CustomEquipment):
            return redirect(url_for('equipment_custom.delete', equipment_id=equipment_id))

        LOGGER.error(f'Could not determine delete url for equipment with id: {equipment_id}')
        abort(404)

    def __create_equipment_groups_for_workout_type(
        workout_type: WorkoutType,
        user_id: int,
        include_bikes: bool,
        equipment_filter_state: EquipmentFilterState,
    ) -> list[EquipmentGroupModel]:
        selectedEquipmentTypes = equipment_filter_state.get_selected_equipment_types()

        result = []
        if include_bikes and EquipmentType.BIKE in selectedEquipmentTypes:
            bikes = [
                item
                for item in bikeService.get_all_statistic_items_by_workout_type(workout_type, user_id)
                if __is_equipment_statistic_item_visible(item, equipment_filter_state)
            ]
            result.append(
                EquipmentGroupModel(
                    icon=Bike.get_icon()[0],
                    is_font_awesome_icon=Bike.get_icon()[1],
                    add_text=gettext('Add bike'),
                    add_url=url_for('equipment_bike.add', workout_type=workout_type.name),
                    items=bikes,
                )
            )

        if EquipmentType.CLOTHES in selectedEquipmentTypes:
            clothes = [
                item
                for item in clothesService.get_all_statistic_items_by_workout_type(workout_type, user_id)
                if __is_equipment_statistic_item_visible(item, equipment_filter_state)
            ]
            clothes.sort(key=lambda item: cast(Clothes, item.equipment).clothes_type.order)
            result.append(
                EquipmentGroupModel(
                    icon=Clothes.get_icon()[0],
                    is_font_awesome_icon=Clothes.get_icon()[1],
                    add_text=gettext('Add clothes'),
                    add_url=url_for('equipment_clothes.add', workout_type=workout_type.name),
                    items=clothes,
                )
            )

        if EquipmentType.CUSTOM in selectedEquipmentTypes:
            custom = [
                item
                for item in customEquipmentService.get_all_statistic_items_by_workout_type(workout_type, user_id)
                if __is_equipment_statistic_item_visible(item, equipment_filter_state)
            ]
            result.append(
                EquipmentGroupModel(
                    icon=CustomEquipment.get_icon()[0],
                    is_font_awesome_icon=Clothes.get_icon()[1],
                    add_text=gettext('Add custom equipment'),
                    add_url=url_for('equipment_custom.add', workout_type=workout_type.name),
                    items=custom,
                )
            )

        return result

    return equipment


def __is_equipment_statistic_item_visible(
    item: EquipmentStatisticModel, equipment_filter_state: EquipmentFilterState
) -> bool:
    equipment = item.equipment

    if equipment.is_active and not equipment_filter_state.is_active_selected:
        return False

    if not equipment.is_active and not equipment_filter_state.is_inactive_selected:
        return False

    if equipment.is_owned and not equipment_filter_state.is_owned_selected:
        return False

    if not equipment.is_owned and not equipment_filter_state.is_owned_selected:
        return False

    if isinstance(equipment, Clothes):
        return equipment.clothes_type in equipment_filter_state.get_selected_clothes_types()

    return True
