from __future__ import annotations

import logging
import os
from datetime import datetime
from io import BytesIO
from typing import Any, TYPE_CHECKING

from sqlalchemy import extract, func, DateTime, String

from sporttracker.monthGoal.MonthGoalService import MonthGoalService

if TYPE_CHECKING:
    from sporttracker.notification.NotificationService import NotificationService

from sporttracker.workout.distance.DistanceWorkoutModel import DistanceWorkoutFormModel

from werkzeug.datastructures import FileStorage

from sporttracker.api.FormModels import DistanceWorkoutApiFormModel
from sporttracker import Constants
from sporttracker.gpx.GpxService import GpxService
from sporttracker.workout.distance.DistanceWorkoutEntity import DistanceWorkout, MonthDistanceSum
from sporttracker.user.ParticipantEntity import get_participants_by_ids
from sporttracker.plannedTour.PlannedTourEntity import PlannedTour
from sporttracker.workout.WorkoutType import WorkoutType
from sporttracker.db import db

from sporttracker.plannedTour.PlannedTourService import PlannedTourService

LOGGER = logging.getLogger(Constants.APP_NAME)


class DistanceWorkoutService:
    def __init__(
        self,
        gpx_service: GpxService,
        temp_folder_path: str,
        tile_hunting_settings: dict[str, Any],
        notification_service: NotificationService,
    ) -> None:
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

        startTime = form_model.calculate_start_time()
        workout = DistanceWorkout(
            name=form_model.name,
            type=WorkoutType(form_model.type),  # type: ignore[call-arg]
            start_time=startTime,
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

        previousLongestDistance = self.get_longest_workout_distance(user_id, workout.type)
        previousCompletedMonthGoals = MonthGoalService.get_goal_summaries_for_completed_goals(
            startTime.year, startTime.month, [workout.type], user_id
        )
        previousBestMonthDistance = DistanceWorkoutService.get_month_distance(
            user_id=user_id,
            workoutType=workout.type,
            year=workout.start_time.year,  # type: ignore[attr-defined]
            month=workout.start_time.month,  # type: ignore[attr-defined]
        )

        db.session.add(workout)
        db.session.commit()

        if gpxMetadataId is not None:
            self._gpx_service.add_visited_tiles_for_workout(
                workout, self._tile_hunting_settings['baseZoomLevel'], user_id
            )

        LOGGER.debug(f'Saved new distance workout: {workout}')
        self._notification_service.on_distance_workout_updated(
            user_id, workout, previousLongestDistance, previousBestMonthDistance
        )
        self._notification_service.on_check_month_goals(user_id, workout, previousCompletedMonthGoals)
        return workout

    def add_workout_via_api(
        self,
        form_model: DistanceWorkoutApiFormModel,
        planned_tour: PlannedTour | None,
        user_id: int,
    ) -> DistanceWorkout:
        participants = get_participants_by_ids(form_model.participants)

        startTime = form_model.calculate_start_time()
        workout = DistanceWorkout(
            name=form_model.name,
            type=WorkoutType(form_model.workout_type),  # type: ignore[call-arg]
            start_time=startTime,
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

        previousLongestDistance = self.get_longest_workout_distance(user_id, workout.type)
        previousCompletedMonthGoals = MonthGoalService.get_goal_summaries_for_completed_goals(
            startTime.year, startTime.month, [workout.type], user_id
        )
        previousBestMonthDistance = DistanceWorkoutService.get_month_distance(
            user_id=user_id,
            workoutType=workout.type,
            year=workout.start_time.year,  # type: ignore[attr-defined]
            month=workout.start_time.month,  # type: ignore[attr-defined]
        )

        db.session.add(workout)
        db.session.commit()

        LOGGER.debug(f'Saved new distance workout: {workout}')
        self._notification_service.on_distance_workout_updated(
            user_id, workout.type, previousLongestDistance, previousBestMonthDistance
        )
        self._notification_service.on_check_month_goals(user_id, workout, previousCompletedMonthGoals)
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
        self._notification_service.on_distance_workout_updated(user_id, workout, None, None)

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

        startTime = form_model.calculate_start_time()
        previousLongestDistance = self.get_longest_workout_distance(user_id, workout.type)
        previousCompletedMonthGoals = MonthGoalService.get_goal_summaries_for_completed_goals(
            startTime.year, startTime.month, [workout.type], user_id
        )
        previousBestMonthDistance = DistanceWorkoutService.get_month_distance(
            user_id=user_id,
            workoutType=workout.type,
            year=workout.start_time.year,  # type: ignore[attr-defined]
            month=workout.start_time.month,  # type: ignore[attr-defined]
        )

        if form_model.planned_tour_id == '-1':
            plannedTour = None
        else:
            plannedTour = PlannedTourService.get_planned_tour_by_id(int(form_model.planned_tour_id))

        workout.name = form_model.name  # type: ignore[assignment]
        workout.start_time = startTime  # type: ignore[assignment]
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
        self._notification_service.on_distance_workout_updated(
            user_id, workout, previousLongestDistance, previousBestMonthDistance
        )
        self._notification_service.on_check_month_goals(user_id, workout, previousCompletedMonthGoals)
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

    @staticmethod
    def get_longest_workout_distance(user_id: int, workout_type: WorkoutType) -> int | None:
        longestWorkout = (
            DistanceWorkout.query.filter(DistanceWorkout.type == workout_type)
            .filter(DistanceWorkout.user_id == user_id)
            .order_by(DistanceWorkout.distance.desc())
            .first()
        )

        if longestWorkout is None:
            return None

        return longestWorkout.distance

    @staticmethod
    def get_distance_per_month_by_type(
        user_id: int, workoutType: WorkoutType, minYear: int, maxYear: int
    ) -> list[MonthDistanceSum]:
        year = extract('year', DistanceWorkout.start_time)
        month = extract('month', DistanceWorkout.start_time)

        rows = (
            DistanceWorkout.query.with_entities(
                func.sum(DistanceWorkout.distance / 1000).label('distanceSum'),
                year.label('year'),
                month.label('month'),
            )
            .filter(DistanceWorkout.type == workoutType)
            .filter(DistanceWorkout.user_id == user_id)
            .group_by(year, month)
            .order_by(year, month)
            .all()
        )

        result = []
        for currentYear in range(minYear, maxYear + 1):
            for currentMonth in range(1, 13):
                for row in rows:
                    if row.year == currentYear and row.month == currentMonth:
                        result.append(
                            MonthDistanceSum(year=currentYear, month=currentMonth, distanceSum=float(row.distanceSum))
                        )
                        break
                else:
                    result.append(MonthDistanceSum(year=currentYear, month=currentMonth, distanceSum=0.0))

        return result

    @staticmethod
    def get_available_years(userId) -> list[int]:
        year = extract('year', DistanceWorkout.start_time)

        rows = (
            DistanceWorkout.query.with_entities(year.label('year'))
            .filter(DistanceWorkout.user_id == userId)
            .group_by(year)
            .order_by(year)
            .all()
        )

        if rows is None:
            return []

        return [int(row.year) for row in rows]

    @staticmethod
    def get_distance_between_dates(
        userId: int,
        startDateTime: datetime | DateTime,
        endDateTime: datetime | DateTime,
        workoutTypes: list[WorkoutType],
        customWorkoutFieldName: str | None = None,
        customWorkoutFieldValue: str | None = None,
    ) -> int:
        query = (
            DistanceWorkout.query.with_entities(func.sum(DistanceWorkout.distance))
            .filter(DistanceWorkout.type.in_(workoutTypes))
            .filter(DistanceWorkout.user_id == userId)
            .filter(DistanceWorkout.start_time.between(startDateTime, endDateTime))
        )

        if customWorkoutFieldName is not None and customWorkoutFieldValue is not None:
            query = query.filter(
                DistanceWorkout.custom_fields[customWorkoutFieldName].astext.cast(String) == customWorkoutFieldValue
            )

        return int(query.scalar() or 0)

    @staticmethod
    def get_month_distance(user_id: int, workoutType: WorkoutType, year: int, month: int) -> int:
        return (
            DistanceWorkout.query.with_entities(func.sum(DistanceWorkout.distance))
            .filter(DistanceWorkout.type == workoutType)
            .filter(DistanceWorkout.user_id == user_id)
            .filter(extract('year', DistanceWorkout.start_time) == year)  # type: ignore[attr-defined]
            .filter(extract('month', DistanceWorkout.start_time) == month)  # type: ignore[attr-defined]
            .scalar()
            or 0
        )
