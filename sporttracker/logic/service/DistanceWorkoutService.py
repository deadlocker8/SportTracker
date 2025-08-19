import logging
import os
from io import BytesIO
from typing import Any

from pydantic import ConfigDict, field_validator
from werkzeug.datastructures import FileStorage

from sporttracker.api.FormModels import DistanceWorkoutApiFormModel
from sporttracker.blueprints.Workouts import BaseWorkoutFormModel
from sporttracker.logic import Constants
from sporttracker.logic.GpxService import GpxService
from sporttracker.logic.model.DistanceWorkout import DistanceWorkout
from sporttracker.logic.model.Participant import get_participants_by_ids
from sporttracker.plannedTour.PlannedTourEntity import PlannedTour
from sporttracker.logic.model.WorkoutType import WorkoutType
from sporttracker.logic.model.db import db
from sporttracker.logic.service.NotificationService import NotificationService
from sporttracker.plannedTour.PlannedTourService import PlannedTourService

LOGGER = logging.getLogger(Constants.APP_NAME)


class DistanceWorkoutFormModel(BaseWorkoutFormModel):
    distance: float
    planned_tour_id: str = '-1'
    elevation_sum: int | None = None
    gpx_file_name: str | None = None
    has_fit_file: bool = False
    share_code: str | None = None
    fit_file_name: str | None = None  # only used during import from FIT file

    model_config = ConfigDict(
        extra='allow',
    )

    @field_validator(*['elevation_sum'], mode='before')
    def elevationSumCheck(cls, value: str, info) -> str | None:
        if isinstance(value, str):
            value = value.strip()
        if value == '':
            return None
        return value


class DistanceWorkoutService:
    def __init__(
        self,
        gpx_service: GpxService,
        temp_folder_path: str,
        tile_hunting_settings: dict[str, Any],
        notification_service: NotificationService,
    ) -> None:
        super().__init__()
        self._gpx_service = gpx_service
        self._temp_folder_path = temp_folder_path
        self._tile_hunting_settings = tile_hunting_settings
        self._notification_service = notification_service

    def add_workout(
        self,
        form_model: DistanceWorkoutFormModel,
        files: dict[str, FileStorage],
        participant_ids: list[int],
        user_id: int,
    ) -> DistanceWorkout:
        if form_model.fit_file_name:  # only filled during import from FIT file
            files = self.__handle_fit_import(form_model)

        gpxMetadataId = self._gpx_service.handle_gpx_upload_for_workout(files)

        participants = get_participants_by_ids(participant_ids)
        if form_model.planned_tour_id == '-1':
            plannedTour = None
        else:
            plannedTour = PlannedTourService.get_planned_tour_by_id(int(form_model.planned_tour_id))

        workout = DistanceWorkout(
            name=form_model.name,
            type=WorkoutType(form_model.type),  # type: ignore[call-arg]
            start_time=form_model.calculate_start_time(),
            duration=form_model.calculate_duration(),
            distance=form_model.distance * 1000,
            average_heart_rate=form_model.average_heart_rate,
            elevation_sum=form_model.elevation_sum,
            gpx_metadata_id=gpxMetadataId,
            custom_fields=form_model.model_extra,
            user_id=user_id,
            participants=participants,
            share_code=form_model.share_code if form_model.share_code else None,
            planned_tour=plannedTour,
        )

        db.session.add(workout)
        db.session.commit()

        if gpxMetadataId is not None:
            self._gpx_service.add_visited_tiles_for_workout(
                workout, self._tile_hunting_settings['baseZoomLevel'], user_id
            )

        LOGGER.debug(f'Saved new distance workout: {workout}')
        self._notification_service.on_distance_workout_updated(user_id, workout.type)
        return workout

    def add_workout_via_api(
        self,
        form_model: DistanceWorkoutApiFormModel,
        planned_tour: PlannedTour | None,
        user_id: int,
    ) -> DistanceWorkout:
        participants = get_participants_by_ids(form_model.participants)

        workout = DistanceWorkout(
            name=form_model.name,
            type=WorkoutType(form_model.workout_type),  # type: ignore[call-arg]
            start_time=form_model.calculate_start_time(),
            duration=form_model.duration,
            distance=form_model.distance,
            average_heart_rate=form_model.average_heart_rate,
            elevation_sum=form_model.elevation_sum,
            gpx_metadata_id=None,
            custom_fields={} if form_model.custom_fields is None else form_model.custom_fields,
            user_id=user_id,
            participants=participants,
            share_code=None,
            planned_tour=planned_tour,
        )

        db.session.add(workout)
        db.session.commit()

        LOGGER.debug(f'Saved new distance workout: {workout}')
        self._notification_service.on_distance_workout_updated(user_id, workout.type)
        return workout

    def __handle_fit_import(self, form_model: DistanceWorkoutFormModel) -> dict[str, FileStorage]:
        fitFilePath = os.path.join(
            self._temp_folder_path, f'{form_model.fit_file_name}.{GpxService.FIT_FILE_EXTENSION}'
        )
        if os.path.exists(fitFilePath):
            with open(fitFilePath, 'rb') as fitFile:
                fitFileContent = BytesIO(fitFile.read())
                file = FileStorage(
                    fitFileContent,
                    f'{form_model.fit_file_name}.{GpxService.FIT_FILE_EXTENSION}',
                    'gpxTrack',
                    'application/octet-stream',
                    0,
                )
            os.remove(fitFilePath)

        return {'gpxTrack': file}  # type: ignore[assignment]

    def delete_workout_by_id(self, workout_id: int, user_id: int) -> None:
        workout = self.get_distance_workout_by_id(workout_id, user_id)

        if workout is None:
            raise ValueError(f'No distance workout with ID {workout_id} found')

        self._gpx_service.delete_gpx(workout, user_id)

        db.session.delete(workout)
        db.session.commit()

        LOGGER.debug(f'Deleted distance workout: {workout}')
        self._notification_service.on_distance_workout_updated(user_id, workout.type)

    def edit_workout(
        self,
        workout_id: int,
        form_model: DistanceWorkoutFormModel,
        files: dict[str, FileStorage],
        participant_ids: list[int],
        user_id: int,
    ) -> DistanceWorkout:
        workout = self.get_distance_workout_by_id(workout_id, user_id)

        if workout is None:
            raise ValueError(f'No distance workout with ID {workout_id} found')

        if form_model.planned_tour_id == '-1':
            plannedTour = None
        else:
            plannedTour = PlannedTourService.get_planned_tour_by_id(int(form_model.planned_tour_id))

        workout.name = form_model.name  # type: ignore[assignment]
        workout.start_time = form_model.calculate_start_time()  # type: ignore[assignment]
        workout.distance = form_model.distance * 1000  # type: ignore[assignment]
        workout.duration = form_model.calculate_duration()  # type: ignore[assignment]
        workout.average_heart_rate = form_model.average_heart_rate  # type: ignore[assignment]
        workout.elevation_sum = form_model.elevation_sum  # type: ignore[assignment]
        workout.participants = get_participants_by_ids(participant_ids)
        workout.share_code = form_model.share_code if form_model.share_code else None  # type: ignore[assignment]
        workout.planned_tour = plannedTour  # type: ignore[assignment]

        shouldUpdateVisitedTiles = False
        newGpxMetadataId = self._gpx_service.handle_gpx_upload_for_workout(files)
        if workout.gpx_metadata_id is None:
            workout.gpx_metadata_id = newGpxMetadataId
            shouldUpdateVisitedTiles = True
        else:
            if newGpxMetadataId is not None:
                self._gpx_service.delete_gpx(workout, user_id)
                workout.gpx_metadata_id = newGpxMetadataId
                shouldUpdateVisitedTiles = True

        workout.custom_fields = form_model.model_extra

        db.session.commit()

        if shouldUpdateVisitedTiles and workout.gpx_metadata_id is not None:
            self._gpx_service.add_visited_tiles_for_workout(
                workout, self._tile_hunting_settings['baseZoomLevel'], user_id
            )

        LOGGER.debug(f'Updated distance workout: {workout}')
        self._notification_service.on_distance_workout_updated(user_id, workout.type)
        return workout

    @staticmethod
    def get_distance_workout_by_id(workout_id: int, user_id: int) -> DistanceWorkout | None:
        return (
            DistanceWorkout.query.filter(DistanceWorkout.user_id == user_id)
            .filter(DistanceWorkout.id == workout_id)
            .first()
        )

    @staticmethod
    def get_distance_workout_by_share_code(shareCode: str) -> DistanceWorkout | None:
        return DistanceWorkout.query.filter(DistanceWorkout.share_code == shareCode).first()
