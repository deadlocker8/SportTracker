import logging
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import text

from sporttracker.logic import Constants
from sporttracker.logic.model.TrackType import TrackType
from sporttracker.logic.model.db import db

LOGGER = logging.getLogger(Constants.APP_NAME)


@dataclass
class NewTilesPerTrack:
    track_id: int
    type: TrackType
    name: str
    startTime: datetime
    numberOfNewTiles: int


class NewVisitedTileCache:
    def __init__(self) -> None:
        self._newVisitedTilesPerUser: dict[str, list[NewTilesPerTrack]] = {}

    @staticmethod
    def __calculate_cache_key(userId: int, trackTypes: list[TrackType], years: list[int]) -> str:
        activeTrackTypes = '_'.join(sorted([t.name for t in trackTypes]))
        activeYears = '_'.join(sorted([str(y) for y in years]))
        return f'{userId}_{activeTrackTypes}_{activeYears}'

    def get_new_visited_tiles_per_track_by_user(
        self, userId: int, trackTypes: list[TrackType], years: list[int]
    ) -> list[NewTilesPerTrack]:
        cacheKey = self.__calculate_cache_key(userId, trackTypes, years)

        if cacheKey not in self._newVisitedTilesPerUser:
            LOGGER.debug(f'Creating entry in NewVisitedTileCache with key {cacheKey}')
            self._newVisitedTilesPerUser[cacheKey] = self.__determine_new_tiles_per_track(
                userId, trackTypes, years
            )

        return self._newVisitedTilesPerUser[cacheKey]

    def invalidate_cache_entry_by_user(self, userId: int) -> None:
        for key in list(self._newVisitedTilesPerUser.keys()):
            if key.startswith(f'{userId}_'):
                LOGGER.debug(f'Invalidating NewVisitedTileCache with key with id {key}')
                del self._newVisitedTilesPerUser[key]

    @staticmethod
    def __determine_new_tiles_per_track(
        userId: int, trackTypes: list[TrackType], years: list[int]
    ) -> list[NewTilesPerTrack]:
        trackTypeOperator = ''
        trackTypeOperator2 = ''
        if trackTypes:
            activeTrackTypes = ','.join([f"'{x.name}'" for x in trackTypes])
            trackTypeOperator = f'AND prev."type" in ({activeTrackTypes})'
            trackTypeOperator2 = f'AND t."type" in ({activeTrackTypes})'

        yearOperator = ''
        yearOperator2 = ''
        if years:
            activeYears = ','.join([f"'{x}'" for x in years])
            yearOperator = f'AND EXTRACT(year FROM prev."startTime") in ({activeYears})'
            yearOperator2 = f'AND EXTRACT(year FROM t."startTime") in ({activeYears})'

        rows = db.session.execute(
            text(f"""SELECT t."id",
               t."type",
               t."name",
               t."startTime",
               (SELECT count(*)
                FROM gpx_visited_tile
                WHERE gpx_visited_tile."track_id" = t."id"
                  AND NOT EXISTS (SELECT
                                  FROM track AS prev
                                           join gpx_visited_tile AS visitied ON prev."id" = visitied."track_id"
                                  WHERE prev."startTime" < t."startTime"
                                    AND prev."user_id" = t."user_id"
                                    AND gpx_visited_tile."x" = visitied."x"
                                    AND gpx_visited_tile."y" = visitied."y"
                                    {trackTypeOperator}
                                    {yearOperator}
                                    )) AS newTiles
        FROM track AS t
        WHERE t."gpx_metadata_id" IS NOT NULL
        AND t."user_id" = {userId}
        {trackTypeOperator2}
        {yearOperator2}
        ORDER BY t."startTime\"""")
        ).fetchall()

        return [NewTilesPerTrack(row[0], TrackType(row[1]), row[2], row[3], row[4]) for row in rows]  # type: ignore[call-arg]
