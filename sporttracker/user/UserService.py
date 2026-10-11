from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sporttracker.gpx.GpxService import GpxService
    from sporttracker.longDistanceTour.LongDistanceTourService import LongDistanceTourService

import logging

from sporttracker import Constants
from sporttracker.db import db
from sporttracker.longDistanceTour.LongDistanceTourEntity import LongDistanceTour
from sporttracker.plannedTour.PlannedTourEntity import PlannedTour
from sporttracker.user.UserEntity import User
from sporttracker.workout.distance.DistanceWorkoutEntity import DistanceWorkout

LOGGER = logging.getLogger(Constants.APP_NAME)


class UserService:
    def __init__(
        self,
        gpx_service: GpxService,
        long_distance_tour_service: LongDistanceTourService,
    ) -> None:
        self._gpx_service = gpx_service
        self._long_distance_tour_service = long_distance_tour_service

    def delete_user(self, user: User) -> None:
        self.__delete_gpx_data_for_user(user.id)
        self.__delete_long_distance_tour_preview_images(user.id)

        LOGGER.debug(f'Deleted user: {user.username}')
        db.session.delete(user)
        db.session.commit()

    def __delete_gpx_data_for_user(self, user_id: int) -> None:
        for distanceWorkout in DistanceWorkout.query.filter(DistanceWorkout.user_id == user_id).all():
            if distanceWorkout.gpx_metadata_id is not None:
                self._gpx_service.delete_gpx(distanceWorkout, user_id)

        for plannedTour in PlannedTour.query.filter(PlannedTour.user_id == user_id).all():
            if plannedTour.gpx_metadata_id is not None:
                self._gpx_service.delete_gpx(plannedTour, user_id)

    def __delete_long_distance_tour_preview_images(self, user_id: int) -> None:
        longDistanceTours = LongDistanceTour.query.filter(LongDistanceTour.user_id == user_id).all()
        for longDistanceTour in longDistanceTours:
            self._long_distance_tour_service.delete_preview_image(longDistanceTour)
