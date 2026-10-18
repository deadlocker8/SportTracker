from __future__ import annotations

import logging

from sporttracker import Constants
from sporttracker.equipment.EquipmentEntity import Equipment

LOGGER = logging.getLogger(Constants.APP_NAME)


class EquipmentService:
    @staticmethod
    def get_equipment_by_id(equipment_id: int, user_id: int) -> Equipment | None:
        return Equipment.query.filter(Equipment.user_id == user_id).filter(Equipment.id == equipment_id).first()
