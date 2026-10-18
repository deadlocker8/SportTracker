from __future__ import annotations

import logging
from datetime import date, datetime
from operator import attrgetter

from natsort import natsort, natsorted

from sporttracker import Constants
from sporttracker.db import db
from sporttracker.equipment.bike.BikeEntity import Bike
from sporttracker.equipment.bike.BikeModel import BikeFormModel
from sporttracker.equipment.EquipmentModel import BaseEquipmentModel
from sporttracker.helpers.DateFormats import DATE_FORMAT_DATE
from sporttracker.workout.WorkoutType import WorkoutType

LOGGER = logging.getLogger(Constants.APP_NAME)


class BikeService:
    @staticmethod
    def add_bike(form_model: BikeFormModel, user_id: int) -> None:
        bike = Bike(
            workout_type=WorkoutType(form_model.workout_type),  # type: ignore[call-arg]
            name=form_model.name,
            purchase_date=form_model.purchase_date,
            is_active=bool(form_model.is_active),
            inactive_date=None if bool(form_model.is_active) else datetime.today(),
            user_id=user_id,
        )

        db.session.add(bike)
        db.session.commit()
        LOGGER.debug(f'Saved new bike: {bike}')

    def update_bike(self, bike_id: int, form_model: BikeFormModel, user_id: int) -> None:
        bike = self.get_bike_by_id(bike_id, user_id)

        if bike is None:
            raise ValueError(f'No bike with ID {bike_id} found')

        bike.workout_type = WorkoutType(form_model.workout_type)  # type: ignore[call-arg]
        bike.name = form_model.name
        bike.purchase_date = date.strptime(form_model.purchase_date, DATE_FORMAT_DATE)
        bike.is_active = bool(form_model.is_active)
        bike.inactive_date = self._parse_inactive_date(form_model)  # type: ignore[assignment]
        db.session.commit()

        LOGGER.debug(f'Updated bike: {bike}')

    def delete_bike(self, bike_id: int, user_id: int) -> None:
        bike = self.get_bike_by_id(bike_id, user_id)

        if bike is None:
            raise ValueError(f'No bike with ID {bike_id} found')

        LOGGER.debug(f'Deleted bike: {bike}')
        db.session.delete(bike)
        db.session.commit()

    @staticmethod
    def get_bike_by_id(equipment_id: int, user_id: int) -> Bike | None:
        return Bike.query.filter(Bike.user_id == user_id).filter(Bike.id == equipment_id).first()

    @staticmethod
    def get_all_bikes_by_workout_type(workout_type: WorkoutType, user_id: int) -> list[BaseEquipmentModel]:
        equipmentEntries = Bike.query.filter(Bike.user_id == user_id).filter(Bike.workout_type == workout_type).all()

        return natsorted(equipmentEntries, alg=natsort.ns.IGNORECASE, key=attrgetter('name'))

    @staticmethod
    def _parse_inactive_date(form_model: BikeFormModel) -> date | None:
        if form_model.is_active:
            return None

        if form_model.inactive_date is None or not form_model.inactive_date:
            return datetime.today()

        return date.strptime(form_model.inactive_date, DATE_FORMAT_DATE)
