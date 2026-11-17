from __future__ import annotations

import logging
from collections import defaultdict

from flask_babel import gettext

from sporttracker import Constants
from sporttracker.equipment.bike.BikeEntity import Bike
from sporttracker.equipment.bike.BikeService import BikeService
from sporttracker.equipment.clothes.ClothesEntity import Clothes
from sporttracker.equipment.clothes.ClothesService import ClothesService
from sporttracker.equipment.custom.CustomEquipmentEntity import CustomEquipment
from sporttracker.equipment.custom.CustomEquipmentService import CustomEquipmentService
from sporttracker.equipment.EquipmentEntity import Equipment
from sporttracker.equipment.EquipmentModel import (
    EquipmentSelectionGroupModel,
    EquipmentSelectionSubGroupModel,
    EquipmentSelectionWorkoutTypeGroupModel,
)
from sporttracker.equipment.EquipmentType import EquipmentType
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
    def get_equipment_grouped_by_workout_type_and_type(
        workout_types: list[WorkoutType], user_id: int, selected_equipment_id: int | None = None
    ) -> dict[WorkoutType, dict[EquipmentType, list[Equipment]]]:
        result = {}

        for workout_type in workout_types:
            equipment_by_type = {}

            equipment_candidates = [
                (EquipmentType.BIKE, BikeService.get_all_by_workout_type(workout_type, user_id)),
                (EquipmentType.CLOTHES, ClothesService.get_all_by_workout_type(workout_type, user_id)),
                (EquipmentType.CUSTOM, CustomEquipmentService.get_all_by_workout_type(workout_type, user_id)),
            ]

            for equipment_type, equipment_items in equipment_candidates:
                available_items = [e for e in equipment_items if e.is_active or e.id == selected_equipment_id]
                if available_items:
                    equipment_by_type[equipment_type] = available_items

            result[workout_type] = equipment_by_type

        return result

    @staticmethod
    def get_selection_groups_by_workout_type(
        workout_type: WorkoutType, user_id: int
    ) -> list[EquipmentSelectionGroupModel]:
        return EquipmentService.__create_selection_groups_for_workout_type(
            workout_type, user_id, include_empty_groups=True
        )

    @staticmethod
    def get_selection_groups_for_all_workout_types(user_id: int) -> list[EquipmentSelectionWorkoutTypeGroupModel]:
        result: list[EquipmentSelectionWorkoutTypeGroupModel] = []
        for workout_type in WorkoutType:
            groups = EquipmentService.__create_selection_groups_for_workout_type(workout_type, user_id)
            result.append(EquipmentSelectionWorkoutTypeGroupModel(workout_type=workout_type, groups=groups))

        return result

    @staticmethod
    def __create_selection_groups_for_workout_type(
        workout_type: WorkoutType, user_id: int, include_empty_groups: bool = False
    ) -> list[EquipmentSelectionGroupModel]:
        groups: list[EquipmentSelectionGroupModel] = []

        bikes = BikeService.get_all_by_workout_type(workout_type, user_id)
        if workout_type == WorkoutType.BIKING and (bikes or include_empty_groups):
            groups.append(
                EquipmentService.__create_selection_group(
                    name=gettext('Bikes'),
                    equipment_class=Bike,
                    items=bikes,
                    sub_groups=[],
                )
            )

        clothes_groups = defaultdict(list)
        for item in ClothesService.get_all_by_workout_type(workout_type, user_id):
            clothes_groups[item.clothes_type].append(item)
        clothes_groups_sorted = dict(sorted(clothes_groups.items(), key=lambda item: item[0].order))
        if clothes_groups_sorted or include_empty_groups:
            groups.append(
                EquipmentService.__create_selection_group(
                    name=gettext('Clothes'),
                    equipment_class=Clothes,
                    items=[],
                    sub_groups=[
                        EquipmentSelectionSubGroupModel(
                            name=key.get_localized_name(), icon=key.icon_file_name, items=value
                        )
                        for key, value in clothes_groups_sorted.items()
                    ],
                )
            )

        custom_equipment = CustomEquipmentService.get_all_by_workout_type(workout_type, user_id)
        if custom_equipment or include_empty_groups:
            groups.append(
                EquipmentService.__create_selection_group(
                    name=gettext('Custom'),
                    equipment_class=CustomEquipment,
                    items=custom_equipment,
                    sub_groups=[],
                )
            )

        return groups

    @staticmethod
    def __create_selection_group(
        name: str,
        equipment_class: type[Equipment],
        items: list[Equipment],
        sub_groups: list[EquipmentSelectionSubGroupModel],
    ) -> EquipmentSelectionGroupModel:
        icon, is_font_awesome_icon = equipment_class.get_icon()

        return EquipmentSelectionGroupModel(
            name=name,
            icon=icon,
            is_font_awesome_icon=is_font_awesome_icon,
            items=items,
            sub_groups=sub_groups,
        )
