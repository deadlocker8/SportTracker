from __future__ import annotations

import logging

from sporttracker import Constants
from sporttracker.db import db
from sporttracker.workout.heartRate.HeartRateEntity import HeartRateEntity

LOGGER = logging.getLogger(Constants.APP_NAME)


class HeartRateService:
    @staticmethod
    def has_heart_rate_data(workout_id: int) -> bool:
        return HeartRateEntity.query.filter(HeartRateEntity.workout_id == workout_id).count() > 0

    @staticmethod
    def get_heart_rate_data(workout_id: int) -> list[HeartRateEntity]:
        return HeartRateEntity.query.filter(HeartRateEntity.workout_id == workout_id).all()

    @staticmethod
    def delete_heart_rate_data(workout_id: int) -> None:
        LOGGER.debug(f'Deleting heart rate data for workout {workout_id}')
        deleteStatement = HeartRateEntity.__table__.delete().where(HeartRateEntity.workout_id == workout_id)
        db.session.execute(deleteStatement)
        db.session.commit()
