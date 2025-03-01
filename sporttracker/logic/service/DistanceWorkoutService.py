import logging
import os
from io import BytesIO
from typing import Any

from pydantic import ConfigDict, field_validator
from werkzeug.datastructures import FileStorage

from sporttracker.blueprints.Workouts import BaseWorkoutFormModel
from sporttracker.logic import Constants
from sporttracker.logic.GpxService import GpxService
from sporttracker.logic.Observable import Observable
from sporttracker.logic.model.DistanceWorkout import DistanceWorkout
from sporttracker.logic.model.Participant import get_participants_by_ids
from sporttracker.logic.model.PlannedTour import get_planned_tour_by_id
from sporttracker.logic.model.WorkoutType import WorkoutType
from sporttracker.logic.model.db import db

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


class DistanceWorkoutService(Observable):
    def __init__(
        self, gpx_service: GpxService, temp_folder_path: str, tile_hunting_settings: dict[str, Any]
    ) -> None:
        super().__init__()
        self._gpx_service = gpx_service
        self._temp_folder_path = temp_folder_path
        self._tile_hunting_settings = tile_hunting_settings

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
            plannedTour = get_planned_tour_by_id(int(form_model.planned_tour_id))

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

        LOGGER.debug(f'Saved new distance workout: {workout}')
        db.session.add(workout)
        db.session.commit()

        if gpxMetadataId is not None:
            self._gpx_service.add_visited_tiles_for_workout(
                workout, self._tile_hunting_settings['baseZoomLevel'], user_id
            )

        self._notify_listeners()

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
