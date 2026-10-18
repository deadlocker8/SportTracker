from __future__ import annotations

import logging
from datetime import date, datetime
from operator import attrgetter

from natsort import natsort, natsorted

from sporttracker import Constants
from sporttracker.db import db
from sporttracker.equipment.clothes.ClothesEntity import Clothes
from sporttracker.equipment.clothes.ClothesModel import ClothesFormModel
from sporttracker.equipment.EquipmentModel import BaseEquipmentModel
from sporttracker.helpers.DateFormats import DATE_FORMAT_DATE
from sporttracker.workout.WorkoutType import WorkoutType

LOGGER = logging.getLogger(Constants.APP_NAME)


class ClothesService:
    @staticmethod
    def add_clothes(form_model: ClothesFormModel, user_id: int) -> None:
        clothes = Clothes(
            workout_type=WorkoutType(form_model.workout_type),  # type: ignore[call-arg]
            name=form_model.name,
            purchase_date=form_model.purchase_date,
            is_active=bool(form_model.is_active),
            inactive_date=None if bool(form_model.is_active) else datetime.today(),
            user_id=user_id,
        )

        db.session.add(clothes)
        db.session.commit()
        LOGGER.debug(f'Saved new clothes: {clothes}')

    def update_clothes(self, clothes_id: int, form_model: ClothesFormModel, user_id: int) -> None:
        clothes = self.get_clothes_by_id(clothes_id, user_id)

        if clothes is None:
            raise ValueError(f'No clothes with ID {clothes_id} found')

        clothes.workout_type = WorkoutType(form_model.workout_type)  # type: ignore[call-arg]
        clothes.name = form_model.name
        clothes.purchase_date = date.strptime(form_model.purchase_date, DATE_FORMAT_DATE)
        clothes.is_active = bool(form_model.is_active)
        clothes.inactive_date = None if bool(form_model.is_active) else datetime.today()  # type: ignore[assignment]
        db.session.commit()

        LOGGER.debug(f'Updated clothes: {clothes}')

    def delete_clothes(self, clothes_id: int, user_id: int) -> None:
        clothes = self.get_clothes_by_id(clothes_id, user_id)

        if clothes is None:
            raise ValueError(f'No clothes with ID {clothes_id} found')

        LOGGER.debug(f'Deleted clothes: {clothes}')
        db.session.delete(clothes)
        db.session.commit()

    @staticmethod
    def get_clothes_by_id(equipment_id: int, user_id: int) -> Clothes | None:
        return Clothes.query.filter(Clothes.user_id == user_id).filter(Clothes.id == equipment_id).first()

    @staticmethod
    def get_all_clothes_by_workout_type(workout_type: WorkoutType, user_id: int) -> list[BaseEquipmentModel]:
        equipmentEntries = (
            Clothes.query.filter(Clothes.user_id == user_id).filter(Clothes.workout_type == workout_type).all()
        )

        return natsorted(equipmentEntries, alg=natsort.ns.IGNORECASE, key=attrgetter('name'))
