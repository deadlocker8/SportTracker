from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sporttracker.plannedTour.PlannedTourService import PlannedTourService
    from sporttracker.notification.NotificationService import NotificationService

import logging
from datetime import datetime
from operator import attrgetter
from typing import Any

import natsort
from flask import request
from flask_login import current_user
from natsort import natsorted
from pydantic import BaseModel
from sqlalchemy.sql import or_

from sporttracker import Constants
from sporttracker.gpx.GpxService import GpxService
from sporttracker.gpx.LongDistanceTourGpxPreviewImageService import LongDistanceTourGpxPreviewImageService
from sporttracker.longDistanceTour.LongDistanceTourEntity import (
    LongDistanceTourPlannedTourAssociation,
    LongDistanceTour,
)
from sporttracker.plannedTour.PlannedTourEntity import PlannedTour
from sporttracker.user.UserEntity import get_users_by_ids, User
from sporttracker.workout.WorkoutType import WorkoutType
from sporttracker.db import db


LOGGER = logging.getLogger(Constants.APP_NAME)


class LongDistanceTourFormModel(BaseModel):
    name: str
    type: str
    sharedUsers: list[str] | str | None = None
    linkedPlannedTours: list[str] | str | None = None


class LongDistanceTourService:
    def __init__(
        self,
        gpx_service: GpxService,
        gpx_preview_image_settings: dict[str, Any],
        planned_tour_service: PlannedTourService,
        notification_service: NotificationService,
    ) -> None:
        self._gpx_service = gpx_service
        self._gpx_preview_image_settings = gpx_preview_image_settings
        self._planned_tour_service = planned_tour_service
        self._notification_service = notification_service

    def add_long_distance_tour(
        self,
        form_model: LongDistanceTourFormModel,
        shared_user_ids: list[int],
        user_id: int,
    ) -> PlannedTour:
        sharedUsers = get_users_by_ids(shared_user_ids)

        longDistanceTour = LongDistanceTour(
            name=form_model.name,
            type=WorkoutType(form_model.type),  # type: ignore[call-arg]
            user_id=user_id,
            creation_date=datetime.now(),
            last_edit_date=datetime.now(),
            last_edit_user_id=user_id,
            shared_users=sharedUsers,
        )

        db.session.add(longDistanceTour)
        db.session.commit()

        longDistanceTour.linked_planned_tours = self.__get_linked_planned_tour_associations(longDistanceTour.id)
        db.session.commit()
        LOGGER.debug(f'Saved new long-distance tour: {longDistanceTour}')

        self.__add_shared_users_to_all_linked_planned_tours(longDistanceTour, sharedUsers)

        gpxPreviewImageService = LongDistanceTourGpxPreviewImageService(
            longDistanceTour, self._gpx_service, self._planned_tour_service
        )
        gpxPreviewImageService.generate_image(self._gpx_preview_image_settings)

        self._notification_service.on_long_distance_tour_created(longDistanceTour)

        return longDistanceTour

    def delete_long_distance_tour_by_id(self, tour_id: int, user_id: int, delete_linked_tours: bool) -> None:
        longDistanceTour = self.get_long_distance_tour_by_id(tour_id)

        if longDistanceTour is None:
            raise ValueError(f'No long-distance tour with ID {tour_id} found')

        if user_id != longDistanceTour.user_id:
            raise ValueError(f'User is not allowed to delete long-distance tour with ID {tour_id}')

        linkedPlannedTours = longDistanceTour.linked_planned_tours

        LOGGER.debug(f'Deleted long-distance tour: {longDistanceTour}')
        db.session.delete(longDistanceTour)
        db.session.commit()

        if delete_linked_tours:
            for linkedPlannedTour in linkedPlannedTours:
                try:
                    self._planned_tour_service.delete_planned_tour_by_id(
                        linkedPlannedTour.planned_tour_id, current_user.id
                    )
                except ValueError as e:
                    LOGGER.error(e)

        self._notification_service.on_long_distance_tour_deleted(longDistanceTour)

    def edit_long_distance_tour(
        self,
        tour_id: int,
        form_model: LongDistanceTourFormModel,
        shared_user_ids: list[int],
        user_id: int,
    ) -> LongDistanceTour:
        longDistanceTour = self.get_long_distance_tour_by_id(tour_id)

        if longDistanceTour is None:
            raise ValueError(f'No long-distance tour with ID {tour_id} found')

        previousSharedUsers = longDistanceTour.shared_users

        longDistanceTour.type = WorkoutType(form_model.type)  # type: ignore[call-arg]
        longDistanceTour.name = form_model.name  # type: ignore[assignment]
        longDistanceTour.last_edit_date = datetime.now()  # type: ignore[assignment]
        longDistanceTour.last_edit_user_id = user_id

        sharedUsers = get_users_by_ids(shared_user_ids)
        longDistanceTour.shared_users = sharedUsers

        longDistanceTour.linked_planned_tours = []
        db.session.commit()
        longDistanceTour.linked_planned_tours = self.__get_linked_planned_tour_associations(tour_id)
        db.session.commit()
        LOGGER.debug(f'Updated long-distance tour: {longDistanceTour}')

        self.__add_shared_users_to_all_linked_planned_tours(longDistanceTour, sharedUsers)

        gpxPreviewImageService = LongDistanceTourGpxPreviewImageService(
            longDistanceTour, self._gpx_service, self._planned_tour_service
        )
        gpxPreviewImageService.generate_image(self._gpx_preview_image_settings)

        self._notification_service.on_long_distance_tour_updated(longDistanceTour, previousSharedUsers)

        return longDistanceTour

    @staticmethod
    def get_long_distance_tour_by_id(tour_id: int) -> LongDistanceTour | None:
        return (
            LongDistanceTour.query.filter(
                or_(
                    LongDistanceTour.user_id == current_user.id,
                    LongDistanceTour.shared_users.any(id=current_user.id),
                )
            )
            .filter(LongDistanceTour.id == tour_id)
            .first()
        )

    @staticmethod
    def get_long_distance_tours(workoutTypes: list[WorkoutType]) -> list[LongDistanceTour]:
        longDistanceTours = (
            LongDistanceTour.query.filter(
                or_(
                    LongDistanceTour.user_id == current_user.id,
                    LongDistanceTour.shared_users.any(id=current_user.id),
                )
            )
            .filter(LongDistanceTour.type.in_(workoutTypes))
            .all()
        )

        return natsorted(longDistanceTours, alg=natsort.ns.IGNORECASE, key=attrgetter('name'))

    @staticmethod
    def __get_linked_planned_tour_associations(tour_id: int) -> list[LongDistanceTourPlannedTourAssociation]:
        linkedPlannedTourIds = [int(item) for item in request.form.getlist('linkedPlannedTours')]
        linkedPlannedTours = []
        for order, linkedPlannedTourId in enumerate(linkedPlannedTourIds):
            linkedPlannedTours.append(
                LongDistanceTourPlannedTourAssociation(
                    long_distance_tour_id=tour_id, planned_tour_id=linkedPlannedTourId, order=order
                )
            )
        return linkedPlannedTours

    def __add_shared_users_to_all_linked_planned_tours(
        self, longDistanceTour: LongDistanceTour, sharedUsers: list[User]
    ) -> None:
        for linkedPlannedTour in longDistanceTour.linked_planned_tours:
            plannedTour = self._planned_tour_service.get_planned_tour_by_id(linkedPlannedTour.planned_tour_id)
            if plannedTour is None:
                continue

            for sharedUser in sharedUsers:
                if sharedUser not in plannedTour.shared_users:
                    plannedTour.shared_users.append(sharedUser)
                    LOGGER.debug(f'Added shared user {sharedUser.id} to linked planned tour {plannedTour.id}')
                db.session.commit()
