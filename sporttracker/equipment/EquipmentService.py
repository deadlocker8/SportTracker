from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime
from operator import attrgetter
from typing import Any

from natsort import natsort, natsorted
from pydantic import field_validator

from sporttracker import Constants
from sporttracker.db import db
from sporttracker.equipment.EquipmentEntity import Equipment
from sporttracker.equipment.EquipmentType import EquipmentType
from sporttracker.helpers.DateFormats import DATE_FORMAT_DATE
from sporttracker.workout.WorkoutType import WorkoutType

LOGGER = logging.getLogger(Constants.APP_NAME)


@dataclass
class EquipmentModel:
    id: int
    type: EquipmentType
    workout_type: WorkoutType
    name: str
    purchase_date: date
    is_active: bool
    inactive_date: date | None

    @staticmethod
    def create_from_equipment(equipment: Equipment) -> EquipmentModel:
        return EquipmentModel(
            id=equipment.id,
            type=equipment.type,
            workout_type=equipment.workout_type,
            name=equipment.name,
            purchase_date=equipment.purchase_date,
            is_active=equipment.is_active,
            inactive_date=equipment.inactive_date,
        )


@dataclass
class EquipmentFormModel:
    name: str
    type: str
    workout_type: str
    purchase_date: str
    is_active: bool

    @field_validator('name', mode='before')
    @classmethod
    def name_strip(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.strip()
        return v


class EquipmentService:
    @staticmethod
    def add_equipment(form_model: EquipmentFormModel, user_id: int) -> None:
        equipment = Equipment(
            type=EquipmentType(form_model.type),  # type: ignore[call-arg]
            workout_type=WorkoutType(form_model.workout_type),  # type: ignore[call-arg]
            name=form_model.name,
            purchase_date=form_model.purchase_date,
            is_active=bool(form_model.is_active),
            inactive_date=None if bool(form_model.is_active) else datetime.today(),
            user_id=user_id,
        )

        db.session.add(equipment)
        db.session.commit()
        LOGGER.debug(f'Saved new equipment: {equipment}')

    def update_equipment(self, equipment_id: int, form_model: EquipmentFormModel, user_id: int) -> None:
        equipment = self.get_equipment_by_id(equipment_id, user_id)

        if equipment is None:
            raise ValueError(f'No equipment with ID {equipment_id} found')

        equipment.type = EquipmentType(form_model.type)  # type: ignore[call-arg]
        equipment.workout_type = WorkoutType(form_model.workout_type)  # type: ignore[call-arg]
        equipment.name = form_model.name
        equipment.purchase_date = date.strptime(form_model.purchase_date, DATE_FORMAT_DATE)
        equipment.is_active = bool(form_model.is_active)
        equipment.inactive_date = None if bool(form_model.is_active) else datetime.today()  # type: ignore[assignment]
        db.session.commit()

        LOGGER.debug(f'Updated equipment: {equipment}')

    def delete_equipment(self, equipment_id: int, user_id: int) -> None:
        equipment = self.get_equipment_by_id(equipment_id, user_id)

        if equipment is None:
            raise ValueError(f'No equipment with ID {equipment_id} found')

        LOGGER.debug(f'Deleted equipment: {equipment}')
        db.session.delete(equipment)
        db.session.commit()

    @staticmethod
    def get_equipment_by_id(equipment_id: int, user_id: int) -> Equipment | None:
        return Equipment.query.filter(Equipment.user_id == user_id).filter(Equipment.id == equipment_id).first()

    @staticmethod
    def get_all_equipment(user_id: int) -> list[Equipment]:
        equipmentEntries = Equipment.query.filter(Equipment.user_id == user_id).all()

        return natsorted(equipmentEntries, alg=natsort.ns.IGNORECASE, key=attrgetter('name'))
