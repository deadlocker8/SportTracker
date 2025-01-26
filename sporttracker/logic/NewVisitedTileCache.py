import logging
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import text

from sporttracker.logic import Constants
from sporttracker.logic.model.WorkoutType import WorkoutType
from sporttracker.logic.model.db import db

LOGGER = logging.getLogger(Constants.APP_NAME)


@dataclass
class NewTilesPerDistanceSport:
    distance_sport_id: int
    type: WorkoutType
    name: str
    startTime: datetime
    numberOfNewTiles: int


class NewVisitedTileCache:
    def __init__(self) -> None:
        self._newVisitedTilesPerUser: dict[str, list[NewTilesPerDistanceSport]] = {}

    @staticmethod
    def __calculate_cache_key(
        userId: int, workoutTypes: list[WorkoutType], years: list[int]
    ) -> str:
        activeTypes = '_'.join(sorted([t.name for t in workoutTypes]))
        activeYears = '_'.join(sorted([str(y) for y in years]))
        return f'{userId}_{activeTypes}_{activeYears}'

    def get_new_visited_tiles_per_track_by_user(
        self, userId: int, workoutTypes: list[WorkoutType], years: list[int]
    ) -> list[NewTilesPerDistanceSport]:
        cacheKey = self.__calculate_cache_key(userId, workoutTypes, years)

        if cacheKey not in self._newVisitedTilesPerUser:
            LOGGER.debug(f'Creating entry in NewVisitedTileCache with key {cacheKey}')
            self._newVisitedTilesPerUser[cacheKey] = self.__determine_new_tiles_per_track(
                userId, workoutTypes, years
            )

        return self._newVisitedTilesPerUser[cacheKey]

    def invalidate_cache_entry_by_user(self, userId: int) -> None:
        for key in list(self._newVisitedTilesPerUser.keys()):
            if key.startswith(f'{userId}_'):
                LOGGER.debug(f'Invalidating NewVisitedTileCache with key with id {key}')
                del self._newVisitedTilesPerUser[key]

    @staticmethod
    def __determine_new_tiles_per_track(
        userId: int, workoutTypes: list[WorkoutType], years: list[int]
    ) -> list[NewTilesPerDistanceSport]:
        workoutTypeOperator = ''
        workoutTypeOperator2 = ''
        if workoutTypes:
            activeWorkoutTypes = ','.join([f"'{x.name}'" for x in workoutTypes])
            workoutTypeOperator = f'AND sp_inner."type" in ({activeWorkoutTypes})'
            workoutTypeOperator2 = f'AND sp."type" in ({activeWorkoutTypes})'

        yearOperator = ''
        yearOperator2 = ''
        if years:
            activeYears = ','.join([f"'{x}'" for x in years])
            yearOperator = f'AND EXTRACT(year FROM sp_inner."start_time") in ({activeYears})'
            yearOperator2 = f'AND EXTRACT(year FROM sp."start_time") in ({activeYears})'

        rows = db.session.execute(
            text(f"""SELECT t."id",
               sp."type",
               sp."name",
               sp."start_time",
               (SELECT count(*)
                FROM gpx_visited_tile
                WHERE gpx_visited_tile."sport_id" = t."id"
                  AND NOT EXISTS (SELECT
                                  FROM distance_sport AS prev
                                           join gpx_visited_tile AS visitied ON prev."id" = visitied."sport_id"
                                  JOIN sport sp_inner ON prev."id" = sp_inner."id"
                                  WHERE sp_inner."start_time" < sp."start_time"
                                    AND sp_inner."user_id" = sp."user_id"
                                    AND gpx_visited_tile."x" = visitied."x"
                                    AND gpx_visited_tile."y" = visitied."y"
                                    {workoutTypeOperator}
                                    {yearOperator}
                                    )) AS newTiles
        FROM distance_sport AS t
        JOIN sport sp ON t."id" = sp."id"
        WHERE t."gpx_metadata_id" IS NOT NULL
        AND sp."user_id" = {userId}
        {workoutTypeOperator2}
        {yearOperator2}
        ORDER BY sp."start_time\"""")
        ).fetchall()

        return [
            NewTilesPerDistanceSport(row[0], WorkoutType(row[1]), row[2], row[3], row[4])  # type: ignore[call-arg]
            for row in rows
        ]
