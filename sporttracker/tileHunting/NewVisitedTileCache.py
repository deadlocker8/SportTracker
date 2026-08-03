import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import text, bindparam

from sporttracker import Constants
from sporttracker.workout.WorkoutType import WorkoutType
from sporttracker.db import db

LOGGER = logging.getLogger(Constants.APP_NAME)


@dataclass
class NewTilesPerDistanceWorkout:
    distance_workout_id: int
    type: WorkoutType
    name: str
    startTime: datetime
    numberOfNewTiles: int


class NewVisitedTileCache:
    def __init__(self) -> None:
        self._newVisitedTilesPerUser: dict[str, list[NewTilesPerDistanceWorkout]] = {}

    @staticmethod
    def __calculate_cache_key(userId: int, workoutTypes: list[WorkoutType], dateRanges: list[tuple[date, date]]) -> str:
        activeTypes = '_'.join(sorted([t.name for t in workoutTypes]))
        activeDateRanges = '_'.join([f'{dateFrom}_{dateTo}' for dateFrom, dateTo in dateRanges])
        return f'{userId}_{activeTypes}_{activeDateRanges}'

    def get_number_of_new_visited_tiles_per_workout_by_user(
        self,
        userId: int,
        workoutTypes: list[WorkoutType],
        dateRanges: list[tuple[date, date]],
    ) -> list[NewTilesPerDistanceWorkout]:
        cacheKey = self.__calculate_cache_key(userId, workoutTypes, dateRanges)

        if cacheKey not in self._newVisitedTilesPerUser:
            LOGGER.debug(f'Creating entry in NewVisitedTileCache with key {cacheKey}')
            self._newVisitedTilesPerUser[cacheKey] = self.__determine_number_of_new_tiles_per_workout(
                userId, workoutTypes, dateRanges
            )

        return self._newVisitedTilesPerUser[cacheKey]

    def invalidate_cache_entry_by_user(self, userId: int) -> None:
        for key in list(self._newVisitedTilesPerUser.keys()):
            if key.startswith(f'{userId}_'):
                LOGGER.debug(f'Invalidating NewVisitedTileCache with key with id {key}')
                del self._newVisitedTilesPerUser[key]

    @staticmethod
    def __determine_number_of_new_tiles_per_workout(
        userId: int,
        workoutTypes: list[WorkoutType],
        dateRanges: list[tuple[date, date]],
    ) -> list[NewTilesPerDistanceWorkout]:
        activeWorkoutTypes = [x.name for x in workoutTypes]

        workoutTypeOperator = ''
        workoutTypeOperator2 = ''
        if workoutTypes:
            workoutTypeOperator = 'AND w_inner."type" in :active_workout_types'
            workoutTypeOperator2 = 'AND w."type" in :active_workout_types'

        dateRangeOperator, dateRangeOperator2, dateRangeParameters = NewVisitedTileCache._build_date_range_operators(
            dateRanges
        )

        # B608 will be disabled because user input is escaped by params, actual f-string is used to build query dynamically
        stmt = text(f"""SELECT t."id",
               w."type",
               w."name",
               w."start_time",
               (SELECT count(*)
                FROM gpx_visited_tile
                WHERE gpx_visited_tile."workout_id" = t."id"
                  AND NOT EXISTS (SELECT
                                  FROM distance_workout AS prev
                                           join gpx_visited_tile AS visitied ON prev."id" = visitied."workout_id"
                                   JOIN workout w_inner ON prev."id" = w_inner."id"
                                   WHERE w_inner."start_time" < w."start_time"
                                     AND w_inner."user_id" = w."user_id"
                                     AND gpx_visited_tile."x" = visitied."x"
                                     AND gpx_visited_tile."y" = visitied."y"
                                     {workoutTypeOperator}
                                     {dateRangeOperator}
                                     )) AS newTiles
        FROM distance_workout AS t
        JOIN workout w ON t."id" = w."id"
        WHERE t."gpx_metadata_id" IS NOT NULL
        AND w."user_id" = :user_id
        {workoutTypeOperator2}
        {dateRangeOperator2}
        ORDER BY w."start_time\"""")  # nosec B608

        if workoutTypeOperator:
            stmt = stmt.bindparams(bindparam('active_workout_types', expanding=True))

        params: dict[str, Any] = {'user_id': userId}
        if workoutTypeOperator:
            params['active_workout_types'] = activeWorkoutTypes
        params.update(dateRangeParameters)

        rows = db.session.execute(stmt, params=params).fetchall()

        return [
            NewTilesPerDistanceWorkout(row[0], WorkoutType(row[1]), row[2], row[3], row[4])  # type: ignore[call-arg]
            for row in rows
        ]

    @staticmethod
    def _build_date_range_operator(columnName: str, dateRanges: list[tuple[date, date]]) -> tuple[str, dict[str, date]]:
        dateRangeClauses = []
        dateRangeParameters: dict[str, date] = {}
        for index, (dateFrom, dateTo) in enumerate(dateRanges):
            dateToExclusive = dateTo + timedelta(days=1)
            fromParameterName = f'date_range_{index}_from'
            toParameterName = f'date_range_{index}_to'
            dateRangeParameters[fromParameterName] = dateFrom
            dateRangeParameters[toParameterName] = dateToExclusive
            dateRangeClauses.append(f'{columnName} >= :{fromParameterName} AND {columnName} < :{toParameterName}')
        return f'AND ({" OR ".join(dateRangeClauses)})', dateRangeParameters

    @staticmethod
    def _build_date_range_operators(
        dateRanges: list[tuple[date, date]],
    ) -> tuple[str, str, dict[str, date]]:
        if not dateRanges:
            return '', '', {}

        dateRangeOperator, dateRangeParameters = NewVisitedTileCache._build_date_range_operator(
            'w_inner."start_time"', dateRanges
        )
        dateRangeOperator2, _ = NewVisitedTileCache._build_date_range_operator('w."start_time"', dateRanges)
        return dateRangeOperator, dateRangeOperator2, dateRangeParameters
