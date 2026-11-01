from __future__ import annotations

import logging

from flask_babel import gettext

from sporttracker import Constants
from sporttracker.equipment.bike.BikeEntity import Bike
from sporttracker.equipment.bike.BikeService import BikeService
from sporttracker.equipment.clothes.ClothesEntity import Clothes
from sporttracker.equipment.clothes.ClothesService import ClothesService
from sporttracker.equipment.custom.CustomEquipmentEntity import CustomEquipment
from sporttracker.equipment.custom.CustomEquipmentService import CustomEquipmentService
from sporttracker.equipment.EquipmentEntity import Equipment
from sporttracker.equipment.EquipmentModel import EquipmentSelectionGroupModel
from sporttracker.workout.WorkoutType import WorkoutType

LOGGER = logging.getLogger(Constants.APP_NAME)


class EquipmentService:
    @staticmethod
    def get_equipment_by_id(equipment_id: int, user_id: int) -> Equipment | None:
        return Equipment.query.filter(Equipment.user_id == user_id).filter(Equipment.id == equipment_id).first()

    @staticmethod
    def get_equipment_by_ids(equipment_ids: list[int], user_id: int, workout_type: WorkoutType) -> list[Equipment]:
        if not equipment_ids:
            return []

        unique_ids = set(equipment_ids)

        return (
            Equipment.query.filter(Equipment.user_id == user_id)
            .filter(Equipment.workout_type == workout_type)
            .filter(Equipment.id.in_(unique_ids))
            .all()
        )

    @staticmethod
    def get_selection_groups_by_workout_type(
        workout_type: WorkoutType, user_id: int
    ) -> list[EquipmentSelectionGroupModel]:
        groups = []

        if workout_type == WorkoutType.BIKING:
            groups.append(
                EquipmentService.__create_selection_group(
                    gettext('Bikes'),
                    Bike,
                    BikeService.get_all_active_by_workout_type(workout_type, user_id),
                )
            )

        groups.append(
            EquipmentService.__create_selection_group(
                gettext('Clothes'),
                Clothes,
                ClothesService.get_all_active_by_workout_type(workout_type, user_id),
            )
        )
        groups.append(
            EquipmentService.__create_selection_group(
                gettext('Custom'),
                CustomEquipment,
                CustomEquipmentService.get_all_active_by_workout_type(workout_type, user_id),
            )
        )

        return groups

    @staticmethod
    def __create_selection_group(
        name: str, equipment_class: type[Equipment], items: list[Equipment]
    ) -> EquipmentSelectionGroupModel:
        icon, is_font_awesome_icon = equipment_class.get_icon()

        return EquipmentSelectionGroupModel(
            name=name,
            icon=icon,
            is_font_awesome_icon=is_font_awesome_icon,
            items=items,
        )
