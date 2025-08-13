import logging
from datetime import datetime
from typing import Any

from flask_login import current_user
from pydantic import BaseModel
from sqlalchemy import tuple_
from werkzeug.datastructures import FileStorage

from sporttracker.logic import Constants
from sporttracker.logic.GpxService import GpxService
from sporttracker.logic.model.DistanceWorkout import DistanceWorkout, get_distance_workout_ids_by_planned_tour
from sporttracker.logic.model.GpxVisitedTile import GpxVisitedTile
from sporttracker.logic.model.LongDistanceTour import LongDistanceTourPlannedTourAssociation
from sporttracker.logic.model.PlannedTour import PlannedTour
from sqlalchemy.sql import or_

from sporttracker.logic.model.TravelType import TravelType
from sporttracker.logic.model.TravelDirection import TravelDirection
from sporttracker.logic.model.User import get_users_by_ids
from sporttracker.logic.model.WorkoutType import WorkoutType
from sporttracker.logic.model.db import db
from sporttracker.logic.service.NotificationService import NotificationService

LOGGER = logging.getLogger(Constants.APP_NAME)


class PlannedTourFormModel(BaseModel):
    name: str
    type: str
    arrivalMethod: str
    departureMethod: str
    direction: str
    sharedUsers: list[str] | str | None = None
    share_code: str | None = None


class PlannedTourEditFormModel(BaseModel):
    name: str
    type: str
    arrivalMethod: TravelType
    departureMethod: TravelType
    direction: TravelDirection
    ownerId: str
    ownerName: str
    sharedUsers: list[str] | str | None = None
    share_code: str | None = None
    gpxFileName: str | None = None
    hasFitFile: bool = False


class PlannedTourService:
    def __init__(
        self,
        gpx_service: GpxService,
        gpx_preview_image_settings: dict[str, Any],
        tile_hunting_settings: dict[str, Any],
        notification_service: NotificationService,
    ) -> None:
        self._gpx_service = gpx_service
        self._gpx_preview_image_settings = gpx_preview_image_settings
        self._tile_hunting_settings = tile_hunting_settings
        self._notification_service = notification_service

    def add_planned_tour(
        self,
        form_model: PlannedTourFormModel,
        files: dict[str, FileStorage],
        shared_user_ids: list[int],
        user_id: int,
    ) -> PlannedTour:
        gpxMetadataId = self._gpx_service.handle_gpx_upload_for_planned_tour(files, self._gpx_preview_image_settings)

        sharedUsers = get_users_by_ids(shared_user_ids)

        plannedTour = PlannedTour(
            name=form_model.name,
            type=WorkoutType(form_model.type),  # type: ignore[call-arg]
            user_id=user_id,
            creation_date=datetime.now(),
            last_edit_date=datetime.now(),
            last_edit_user_id=user_id,
            gpx_metadata_id=gpxMetadataId,
            shared_users=sharedUsers,
            arrival_method=TravelType(form_model.arrivalMethod),  # type: ignore[call-arg]
            departure_method=TravelType(form_model.departureMethod),  # type: ignore[call-arg]
            direction=TravelDirection(form_model.direction),  # type: ignore[call-arg]
            share_code=form_model.share_code if form_model.share_code else None,
        )

        db.session.add(plannedTour)
        db.session.commit()

        if gpxMetadataId is not None:
            self._gpx_service.add_planned_tiles_for_planned_tour(
                plannedTour, self._tile_hunting_settings['baseZoomLevel'], user_id
            )

        LOGGER.debug(f'Saved new planned tour: {plannedTour}')

        linkedLongDistanceTours = LongDistanceTourPlannedTourAssociation.query.filter(
            LongDistanceTourPlannedTourAssociation.planned_tour_id == plannedTour.id
        ).all()
        self.__update_gpx_preview_image_for_long_distance_tours(
            [t.long_distance_tour_id for t in linkedLongDistanceTours]
        )
        self._notification_service.on_planned_tour_created(plannedTour)

        return plannedTour

    def delete_planned_tour_by_id(self, tour_id: int, user_id: int) -> None:
        plannedTour = self.get_planned_tour_by_id(tour_id)

        if plannedTour is None:
            raise ValueError(f'No planned tour with ID {tour_id} found')

        if user_id != plannedTour.user_id:
            raise ValueError(f'User is not allowed to delete planned tour with ID {tour_id}')

        self._gpx_service.delete_gpx(plannedTour, user_id)

        linkedIds = get_distance_workout_ids_by_planned_tour(plannedTour)
        for workoutId in linkedIds:
            workout = DistanceWorkout.query.filter().filter(DistanceWorkout.id == workoutId).first()
            workout.planned_tour = None
            LOGGER.debug(f'Removed linked planned tour from workout: {workoutId}')
            db.session.commit()

        associatedLongDistanceTours = (
            LongDistanceTourPlannedTourAssociation.query.filter()
            .filter(LongDistanceTourPlannedTourAssociation.planned_tour_id == tour_id)
            .all()
        )
        linkedLongDistanceTourIds = [t.long_distance_tour_id for t in associatedLongDistanceTours]
        for association in associatedLongDistanceTours:
            LOGGER.debug(f'Removed planned tour from long-distance tour: {association.long_distance_tour_id}')
            db.session.delete(association)
            db.session.commit()

        self.__update_gpx_preview_image_for_long_distance_tours(linkedLongDistanceTourIds)

        LOGGER.debug(f'Deleted planned tour: {plannedTour}')
        db.session.delete(plannedTour)
        db.session.commit()

        self._notification_service.on_planned_tour_deleted(plannedTour)

    def edit_planned_tour(
        self,
        tour_id: int,
        form_model: PlannedTourFormModel,
        files: dict[str, FileStorage],
        shared_user_ids: list[int],
        user_id: int,
    ) -> PlannedTour:
        plannedTour = self.get_planned_tour_by_id(tour_id)

        if plannedTour is None:
            raise ValueError(f'No planned tour with ID {tour_id} found')

        previousSharedUsers = plannedTour.shared_users

        plannedTour.type = WorkoutType(form_model.type)  # type: ignore[call-arg]
        plannedTour.name = form_model.name  # type: ignore[assignment]
        plannedTour.last_edit_date = datetime.now()  # type: ignore[assignment]
        plannedTour.last_edit_user_id = user_id
        plannedTour.arrival_method = TravelType(form_model.arrivalMethod)  # type: ignore[call-arg]
        plannedTour.departure_method = TravelType(form_model.departureMethod)  # type: ignore[call-arg]
        plannedTour.direction = TravelDirection(form_model.direction)  # type: ignore[call-arg]
        plannedTour.share_code = form_model.share_code if form_model.share_code else None  # type: ignore[assignment]

        shouldUpdateVisitedTiles = False
        newGpxMetadataId = self._gpx_service.handle_gpx_upload_for_planned_tour(files, self._gpx_preview_image_settings)
        if plannedTour.gpx_metadata_id is None:
            plannedTour.gpx_metadata_id = newGpxMetadataId
            shouldUpdateVisitedTiles = True
        else:
            if newGpxMetadataId is not None:
                self._gpx_service.delete_gpx(plannedTour, user_id)
                plannedTour.gpx_metadata_id = newGpxMetadataId

                linkedLongDistanceTours = LongDistanceTourPlannedTourAssociation.query.filter(
                    LongDistanceTourPlannedTourAssociation.planned_tour_id == plannedTour.id
                ).all()
                self.__update_gpx_preview_image_for_long_distance_tours(
                    [t.long_distance_tour_id for t in linkedLongDistanceTours]
                )
                shouldUpdateVisitedTiles = True

        sharedUsers = get_users_by_ids(shared_user_ids)
        plannedTour.shared_users = sharedUsers

        # The list of shared users may have changed.
        # All workouts that link to this planned tour must be checked, whether they are owned by the owner of the
        # planned tour or if the planned tour is still shared to the owner of the workout.
        linkedIds = get_distance_workout_ids_by_planned_tour(plannedTour)
        for workoutId in linkedIds:
            workout = DistanceWorkout.query.filter().filter(DistanceWorkout.id == workoutId).first()
            if workout.user_id == plannedTour.user_id:
                continue

            if workout.user_id in shared_user_ids:
                continue

            workout.planned_tour = None
            LOGGER.debug(f'Removed linked planned tour from workout: {workoutId}')
            db.session.commit()

        LOGGER.debug(f'Updated planned tour: {plannedTour}')
        db.session.commit()

        if shouldUpdateVisitedTiles and plannedTour.gpx_metadata_id is not None:
            self._gpx_service.add_planned_tiles_for_planned_tour(
                plannedTour, self._tile_hunting_settings['baseZoomLevel'], user_id
            )

        self._notification_service.on_planned_tour_updated(plannedTour, previousSharedUsers)

        return plannedTour

    @staticmethod
    def get_planned_tour_by_id(tour_id: int) -> PlannedTour | None:
        return (
            PlannedTour.query.filter(
                or_(
                    PlannedTour.user_id == current_user.id,
                    PlannedTour.shared_users.any(id=current_user.id),
                )
            )
            .filter(PlannedTour.id == tour_id)
            .first()
        )

    @staticmethod
    def get_planned_tour_by_share_code(shareCode: str) -> PlannedTour | None:
        return PlannedTour.query.filter(PlannedTour.share_code == shareCode).first()

    def __update_gpx_preview_image_for_long_distance_tours(self, linkedLongDistanceTourIds: list[int]):
        from sporttracker.logic.service.LongDistanceTourService import LongDistanceTourService

        for linkedLongDistanceTourId in linkedLongDistanceTourIds:
            longDistanceTour = LongDistanceTourService.get_long_distance_tour_by_id(linkedLongDistanceTourId)
            if longDistanceTour is None:
                continue

            from sporttracker.logic.LongDistanceTourGpxPreviewImageService import LongDistanceTourGpxPreviewImageService

            gpxPreviewImageService = LongDistanceTourGpxPreviewImageService(longDistanceTour, self._gpx_service)
            gpxPreviewImageService.generate_image(self._gpx_preview_image_settings)

    def get_number_of_new_visited_tiles(self, plannedTour: PlannedTour) -> int:
        gpxMetadata = plannedTour.get_gpx_metadata()
        if gpxMetadata is None:
            return 0

        newVisitedTiles = self._gpx_service.get_visited_tiles(
            gpxMetadata.gpx_file_name, self._tile_hunting_settings['baseZoomLevel']
        )
        newVisitedTilesTuples = [(v.x, v.y) for v in newVisitedTiles]

        numberOfAlreadyVisitedTiles = (
            DistanceWorkout.query.select_from(DistanceWorkout)
            .join(GpxVisitedTile, GpxVisitedTile.workout_id == DistanceWorkout.id)
            .with_entities(GpxVisitedTile.x, GpxVisitedTile.y)
            .filter(DistanceWorkout.user_id == current_user.id)
            .filter(tuple_(GpxVisitedTile.x, GpxVisitedTile.y).in_(newVisitedTilesTuples))
            .distinct()
            .count()
        )

        return len(newVisitedTiles) - numberOfAlreadyVisitedTiles
