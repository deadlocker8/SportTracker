from dataclasses import dataclass
from datetime import datetime

from flask_login import current_user
from sqlalchemy import extract, text
from sqlalchemy.orm import aliased

from sporttracker.logic.QuickFilterState import QuickFilterState
from sporttracker.logic.model.GpxVisitedTiles import GpxVisitedTile
from sporttracker.logic.model.Track import Track
from sporttracker.logic.model.TrackType import TrackType
from sporttracker.logic.model.db import db


@dataclass
class TileColorPosition:
    tile_color: str
    x: int
    y: int


@dataclass
class NewTilesPerTrack:
    track_id: int
    type: TrackType
    name: str
    startTime: datetime
    numberOfNewTiles: int


class VisitedTileService:
    def __init__(
        self,
        quickFilterState: QuickFilterState,
        yearFilterState: list[int],
        trackId: int | None = None,
    ):
        self._quickFilterState = quickFilterState
        self._yearFilterState = yearFilterState
        self._trackId = trackId

    def calculate_total_number_of_visited_tiles(
        self,
    ) -> int:
        trackAlias = aliased(Track)
        gpxVisitedTileAlias = aliased(GpxVisitedTile)

        return (
            trackAlias.query.select_from(trackAlias)
            .join(gpxVisitedTileAlias, gpxVisitedTileAlias.track_id == trackAlias.id)
            .filter(trackAlias.user_id == current_user.id)
            .filter(trackAlias.type.in_(self._quickFilterState.get_active_types()))
            .filter(extract('year', trackAlias.startTime).in_(self._yearFilterState))
            .distinct(gpxVisitedTileAlias.x, gpxVisitedTileAlias.y)
            .count()
        )

    def determine_tile_colors_of_tracks_that_visit_tiles(
        self, min_x: int, max_x: int, min_y: int, max_y: int
    ) -> list[TileColorPosition]:
        if self._trackId is None:
            return self.__determine_tile_colors_of_all_tracks_that_visit_tiles(
                min_x, max_x, min_y, max_y
            )

        return self.__determine_tile_colors_of_single_track(
            min_x, max_x, min_y, max_y, self._trackId
        )

    def __determine_tile_colors_of_all_tracks_that_visit_tiles(
        self, min_x: int, max_x: int, min_y: int, max_y: int
    ) -> list[TileColorPosition]:
        trackAlias = aliased(Track)
        gpxVisitedTileAlias = aliased(GpxVisitedTile)

        rows = (
            trackAlias.query.select_from(trackAlias)
            .join(gpxVisitedTileAlias, gpxVisitedTileAlias.track_id == trackAlias.id)
            .with_entities(trackAlias.type, gpxVisitedTileAlias.x, gpxVisitedTileAlias.y)
            .filter(trackAlias.user_id == current_user.id)
            .filter(trackAlias.type.in_(self._quickFilterState.get_active_types()))
            .filter(extract('year', trackAlias.startTime).in_(self._yearFilterState))
            .filter(gpxVisitedTileAlias.x >= min_x)
            .filter(gpxVisitedTileAlias.x <= max_x)
            .filter(gpxVisitedTileAlias.y >= min_y)
            .filter(gpxVisitedTileAlias.y <= max_y)
            .group_by(gpxVisitedTileAlias.x, gpxVisitedTileAlias.y, trackAlias.type)
            .all()
        )

        return [TileColorPosition(r[0].tile_color, r[1], r[2]) for r in rows]

    def __determine_tile_colors_of_single_track(
        self, min_x: int, max_x: int, min_y: int, max_y: int, trackId: int
    ) -> list[TileColorPosition]:
        trackAlias = aliased(Track)
        gpxVisitedTileAlias = aliased(GpxVisitedTile)

        rows = (
            trackAlias.query.select_from(trackAlias)
            .join(gpxVisitedTileAlias, gpxVisitedTileAlias.track_id == trackAlias.id)
            .with_entities(trackAlias.type, gpxVisitedTileAlias.x, gpxVisitedTileAlias.y)
            .filter(trackAlias.user_id == current_user.id)
            .filter(trackAlias.id == trackId)
            .filter(gpxVisitedTileAlias.x >= min_x)
            .filter(gpxVisitedTileAlias.x <= max_x)
            .filter(gpxVisitedTileAlias.y >= min_y)
            .filter(gpxVisitedTileAlias.y <= max_y)
            .group_by(gpxVisitedTileAlias.x, gpxVisitedTileAlias.y, trackAlias.type)
            .all()
        )

        return [TileColorPosition(r[0].tile_color, r[1], r[2]) for r in rows]

    def determine_new_tiles_per_track(self) -> list[NewTilesPerTrack]:
        activeTrackTypes = ','.join(
            [f"'{x.name}'" for x in self._quickFilterState.get_active_types()]
        )
        activeYears = ','.join([f"'{x}'" for x in self._yearFilterState])

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
        AND t."user_id" = {current_user.id}
        AND t."type" in ({activeTrackTypes})
        AND EXTRACT(year FROM t."startTime") in ({activeYears})
        ORDER BY t."startTime\"""")
        ).fetchall()

        return [NewTilesPerTrack(row[0], TrackType(row[1]), row[2], row[3], row[4]) for row in rows]  # type: ignore[call-arg]
