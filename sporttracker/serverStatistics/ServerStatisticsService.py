from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import asc, distinct, func

from sporttracker.bodyWeight.BodyWeightEntity import BodyWeight
from sporttracker.db import db
from sporttracker.gpx.GpxMetadataEntity import GpxMetadata
from sporttracker.gpx.GpxService import GpxService
from sporttracker.longDistanceTour.LongDistanceTourEntity import LongDistanceTour
from sporttracker.maintenance.MaintenanceEntity import Maintenance
from sporttracker.maintenance.MaintenanceEventInstanceEntity import MaintenanceEventInstance
from sporttracker.metrics.LoadStatisticsCollector import LoadStatisticsCollector
from sporttracker.monthGoal.MonthGoalEntity import MonthGoalCount, MonthGoalDistance, MonthGoalDuration
from sporttracker.plannedTour.PlannedTourEntity import (
    PlannedTour,
    distance_workout_planned_tour_association,
)
from sporttracker.tileHunting.GpxVisitedTileEntity import GpxVisitedTile
from sporttracker.user.UserEntity import User
from sporttracker.workout.distance.DistanceWorkoutEntity import DistanceWorkout
from sporttracker.workout.WorkoutEntity import Workout
from sporttracker.workout.WorkoutType import WorkoutType


@dataclass
class GlobalStatistics:
    numberOfUsers: int
    numberOfWorkouts: int
    numberOfGpxTracks: int
    totalGpxFileSize: int
    numberOfPreviewImages: int
    numberOfWorkoutsByType: dict[WorkoutType, int]


@dataclass
class UserStatistics:
    username: str
    numberOfWorkouts: int
    numberOfGpxTracks: int
    totalGpxFileSize: int
    numberOfPreviewImages: int
    firstWorkoutDate: datetime | None
    lastWorkoutDate: datetime | None
    numberOfPlannedTours: int
    numberOfCompletedPlannedTours: int
    numberOfVisitedTiles: int
    numberOfBodyWeightEntries: int
    numberOfMonthGoals: int
    numberOfMaintenances: int
    numberOfMaintenanceEvents: int


@dataclass
class CacheCalculationStatistics:
    cacheName: str
    username: str
    workoutTypes: str
    dateRanges: str
    durationSeconds: float


class ServerStatisticsService:
    def __init__(self, dataPath: str, loadStatisticsCollector: LoadStatisticsCollector) -> None:
        self._dataPath = dataPath
        self._loadStatisticsCollector = loadStatisticsCollector

    def get_global_statistics(self) -> GlobalStatistics:
        gpxMetadataList = GpxMetadata.query.all()

        return GlobalStatistics(
            numberOfUsers=User.query.count(),
            numberOfWorkouts=Workout.query.count(),
            numberOfGpxTracks=len(gpxMetadataList),
            totalGpxFileSize=sum(self.__get_gpx_file_size(x.gpx_file_name) for x in gpxMetadataList),
            numberOfPreviewImages=self.__count_preview_images(),
            numberOfWorkoutsByType={
                workoutType: Workout.query.filter(Workout.type == workoutType).count() for workoutType in WorkoutType
            },
        )

    def get_user_statistics(self) -> list[UserStatistics]:
        users = User.query.order_by(asc(func.lower(User.username))).all()

        return [self.__get_statistics_for_user(user) for user in users]

    def get_cache_calculation_statistics(self) -> list[CacheCalculationStatistics]:
        usernamesById = {user.id: user.username for user in User.query.all()}

        statistics: list[CacheCalculationStatistics] = []
        for calculationTime in self._loadStatisticsCollector.get_cache_calculation_times():
            workoutTypes = ', '.join([x.get_localized_name() for x in calculationTime.workoutTypes])
            if calculationTime.dateRanges is None:
                dateRanges = '-'
            else:
                dateRanges = ', '.join([f'{dateFrom} - {dateTo}' for dateFrom, dateTo in calculationTime.dateRanges])

            statistics.append(
                CacheCalculationStatistics(
                    cacheName=calculationTime.cacheName,
                    username=usernamesById.get(calculationTime.userId, str(calculationTime.userId)),
                    workoutTypes=workoutTypes,
                    dateRanges=dateRanges,
                    durationSeconds=calculationTime.durationSeconds,
                )
            )

        statistics.sort(key=lambda x: (x.cacheName, -x.durationSeconds))
        return statistics

    def __get_statistics_for_user(self, user: User) -> UserStatistics:
        distanceWorkouts = (
            DistanceWorkout.query.filter(DistanceWorkout.user_id == user.id)
            .filter(DistanceWorkout.gpx_metadata_id.isnot(None))
            .all()
        )
        plannedTours = PlannedTour.query.filter(PlannedTour.user_id == user.id).all()
        longDistanceTours = LongDistanceTour.query.filter(LongDistanceTour.user_id == user.id).all()

        gpxFileNames = self.__collect_gpx_file_names(distanceWorkouts, plannedTours)
        firstWorkoutDate, lastWorkoutDate = self.__get_workout_date_range(user.id)

        return UserStatistics(
            username=user.username,
            numberOfWorkouts=Workout.query.filter(Workout.user_id == user.id).count(),
            numberOfGpxTracks=len(gpxFileNames),
            totalGpxFileSize=sum(self.__get_gpx_file_size(name) for name in gpxFileNames),
            numberOfPreviewImages=self.__count_user_preview_images(plannedTours, longDistanceTours),
            firstWorkoutDate=firstWorkoutDate,
            lastWorkoutDate=lastWorkoutDate,
            numberOfPlannedTours=len(plannedTours),
            numberOfCompletedPlannedTours=self.__count_completed_planned_tours(
                [tour.id for tour in plannedTours], user.id
            ),
            numberOfVisitedTiles=self.__count_visited_tiles(user.id),
            numberOfBodyWeightEntries=BodyWeight.query.filter(BodyWeight.user_id == user.id).count(),
            numberOfMonthGoals=self.__count_month_goals(user.id),
            numberOfMaintenances=Maintenance.query.filter(Maintenance.user_id == user.id).count(),
            numberOfMaintenanceEvents=MaintenanceEventInstance.query.join(Maintenance)
            .filter(Maintenance.user_id == user.id)
            .count(),
        )

    @staticmethod
    def __collect_gpx_file_names(distanceWorkouts: list[DistanceWorkout], plannedTours: list[PlannedTour]) -> list[str]:
        gpxFileNames = []

        for distanceWorkout in distanceWorkouts:
            gpxMetadata = distanceWorkout.get_gpx_metadata()
            if gpxMetadata is not None:
                gpxFileNames.append(gpxMetadata.gpx_file_name)

        for plannedTour in plannedTours:
            gpxMetadata = plannedTour.get_gpx_metadata()
            if gpxMetadata is not None:
                gpxFileNames.append(gpxMetadata.gpx_file_name)

        return gpxFileNames

    def __count_user_preview_images(
        self, plannedTours: list[PlannedTour], longDistanceTours: list[LongDistanceTour]
    ) -> int:
        count = 0

        for plannedTour in plannedTours:
            gpxMetadata = plannedTour.get_gpx_metadata()
            if gpxMetadata is not None and self.__is_preview_image_existing(gpxMetadata.gpx_file_name):
                count += 1

        for longDistanceTour in longDistanceTours:
            if self.__is_long_distance_tour_preview_image_existing(longDistanceTour.id):
                count += 1

        return count

    @staticmethod
    def __get_workout_date_range(userId: int) -> tuple[datetime | None, datetime | None]:
        result = (
            db.session.query(func.min(Workout.start_time), func.max(Workout.start_time))
            .filter(Workout.user_id == userId)
            .one()
        )

        return result[0], result[1]

    @staticmethod
    def __count_completed_planned_tours(plannedTourIds: list[int], userId: int) -> int:
        if not plannedTourIds:
            return 0

        subquery = (
            db.session.query(distinct(distance_workout_planned_tour_association.c.planned_tour_id))
            .join(
                DistanceWorkout,
                DistanceWorkout.id == distance_workout_planned_tour_association.c.distance_workout_id,
            )
            .filter(distance_workout_planned_tour_association.c.planned_tour_id.in_(plannedTourIds))
            .filter(DistanceWorkout.user_id == userId)
            .subquery()
        )

        return db.session.query(func.count()).select_from(subquery).scalar() or 0

    @staticmethod
    def __count_visited_tiles(userId: int) -> int:
        subquery = (
            db.session.query(GpxVisitedTile.x, GpxVisitedTile.y)
            .join(DistanceWorkout, DistanceWorkout.id == GpxVisitedTile.workout_id)
            .filter(DistanceWorkout.user_id == userId)
            .distinct()
            .subquery()
        )

        return db.session.query(func.count()).select_from(subquery).scalar() or 0

    @staticmethod
    def __count_month_goals(userId: int) -> int:
        return (
            MonthGoalDistance.query.filter(MonthGoalDistance.user_id == userId).count()
            + MonthGoalCount.query.filter(MonthGoalCount.user_id == userId).count()
            + MonthGoalDuration.query.filter(MonthGoalDuration.user_id == userId).count()
        )

    def __get_gpx_folder_path(self, gpxFileName: str) -> str:
        return os.path.join(self._dataPath, gpxFileName)

    def __get_gpx_file_size(self, gpxFileName: str | None) -> int:
        if gpxFileName is None:
            return 0

        folderPath = self.__get_gpx_folder_path(gpxFileName)

        gpxZipFilePath = os.path.join(folderPath, f'{gpxFileName}.{GpxService.ZIP_FILE_EXTENSION}')
        fitFilePath = os.path.join(folderPath, f'{gpxFileName}.{GpxService.FIT_FILE_EXTENSION}')

        totalSize = 0
        if os.path.exists(gpxZipFilePath):
            totalSize += os.path.getsize(gpxZipFilePath)

        if os.path.exists(fitFilePath):
            totalSize += os.path.getsize(fitFilePath)

        return totalSize

    def __is_preview_image_existing(self, gpxFileName: str | None) -> bool:
        if gpxFileName is None:
            return False

        return os.path.exists(os.path.join(self.__get_gpx_folder_path(gpxFileName), f'{gpxFileName}.jpg'))

    def __is_long_distance_tour_preview_image_existing(self, longDistanceTourId: int) -> bool:
        uniqueName = f'long_distance_tour_{longDistanceTourId}'
        return os.path.exists(os.path.join(self.__get_gpx_folder_path(uniqueName), f'{uniqueName}.jpg'))

    def __count_preview_images(self) -> int:
        count = 0

        plannedTours = PlannedTour.query.filter(PlannedTour.gpx_metadata_id.isnot(None)).all()
        for plannedTour in plannedTours:
            gpxMetadata = plannedTour.get_gpx_metadata()
            if gpxMetadata is not None and self.__is_preview_image_existing(gpxMetadata.gpx_file_name):
                count += 1

        longDistanceTours = LongDistanceTour.query.all()
        for longDistanceTour in longDistanceTours:
            if self.__is_long_distance_tour_preview_image_existing(longDistanceTour.id):
                count += 1

        return count
