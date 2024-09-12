from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import text

from sporttracker.logic.model.TrackType import TrackType
from sporttracker.logic.model.db import db


@dataclass
class NewTilesPerTrack:
    track_id: int
    type: TrackType
    name: str
    startTime: datetime
    numberOfNewTiles: int


class NewVisitedTileCache:
    def __init__(self) -> None:
        self._newVisitedTilesPerUser: dict[int, list[NewTilesPerTrack]] = {}

    def get_new_visited_tiles_per_track_by_user(self, userId: int) -> list[NewTilesPerTrack]:
        if userId not in self._newVisitedTilesPerUser:
            self._newVisitedTilesPerUser[userId] = self.__determine_new_tiles_per_track(userId)

        return self._newVisitedTilesPerUser[userId]

    @staticmethod
    def __determine_new_tiles_per_track(userId: int) -> list[NewTilesPerTrack]:
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
                                    AND gpx_visited_tile."y" = visitied."y")) AS newTiles
        FROM track AS t
        WHERE t."gpx_metadata_id" IS NOT NULL
        AND t."user_id" = {userId}
        ORDER BY t."startTime\"""")
        ).fetchall()

        return [NewTilesPerTrack(row[0], TrackType(row[1]), row[2], row[3], row[4]) for row in rows]  # type: ignore[call-arg]
