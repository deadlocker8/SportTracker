from __future__ import annotations

import logging
from operator import attrgetter

from natsort import natsort, natsorted

from sporttracker import Constants
from sporttracker.db import db
from sporttracker.equipment.EquipmentService import EquipmentService
from sporttracker.equipment.presets.EquipmentPresetEntity import EquipmentPreset
from sporttracker.workout.WorkoutType import WorkoutType

LOGGER = logging.getLogger(Constants.APP_NAME)


class EquipmentPresetService:
    @staticmethod
    def get_all_by_workout_type(workout_type: WorkoutType, user_id: int) -> list[EquipmentPreset]:
        presets = (
            EquipmentPreset.query.filter(EquipmentPreset.user_id == user_id)
            .filter(EquipmentPreset.workout_type == workout_type)
            .all()
        )

        return natsorted(presets, alg=natsort.ns.IGNORECASE, key=attrgetter('name'))

    @staticmethod
    def get_by_id(preset_id: int, user_id: int) -> EquipmentPreset | None:
        return (
            EquipmentPreset.query.filter(EquipmentPreset.user_id == user_id)
            .filter(EquipmentPreset.id == preset_id)
            .first()
        )

    @staticmethod
    def add(name: str, workout_type: WorkoutType, equipment_ids: list[int], user_id: int) -> EquipmentPreset:
        equipment = EquipmentService.get_equipment_by_ids(equipment_ids, user_id, workout_type)

        preset = EquipmentPreset(user_id=user_id, workout_type=workout_type, name=name, equipment=equipment)
        db.session.add(preset)
        db.session.commit()
        LOGGER.debug(f'Saved new equipment preset: {preset}')

        return preset

    @staticmethod
    def edit(preset_id: int, name: str, equipment_ids: list[int], user_id: int) -> None:
        preset = EquipmentPresetService.__get_or_raise(preset_id, user_id)
        equipment = EquipmentService.get_equipment_by_ids(equipment_ids, user_id, preset.workout_type)

        preset.name = name
        preset.equipment = equipment
        db.session.commit()

        LOGGER.debug(f'Updated equipment preset: {preset}')

    @staticmethod
    def delete(preset_id: int, user_id: int) -> None:
        preset = EquipmentPresetService.__get_or_raise(preset_id, user_id)

        LOGGER.debug(f'Deleted equipment preset: {preset}')
        preset.equipment = []
        db.session.delete(preset)
        db.session.commit()

    @staticmethod
    def __get_or_raise(preset_id: int, user_id: int) -> EquipmentPreset:
        preset = EquipmentPresetService.get_by_id(preset_id, user_id)

        if preset is None:
            raise ValueError(f'No equipment preset with ID {preset_id} found')

        return preset
