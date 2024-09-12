from dataclasses import dataclass

from flask_login import current_user
from sqlalchemy import extract
from sqlalchemy.orm import aliased

from sporttracker.logic.NewVisitedTileCache import NewTilesPerTrack, NewVisitedTileCache
from sporttracker.logic.QuickFilterState import QuickFilterState
from sporttracker.logic.model.GpxVisitedTiles import GpxVisitedTile
from sporttracker.logic.model.Track import Track


@dataclass
class TileColorPosition:
    tile_color: str
    x: int
    y: int


class VisitedTileService:
    def __init__(
        self,
        newVisitedTileCache: NewVisitedTileCache,
        quickFilterState: QuickFilterState,
        yearFilterState: list[int],
        trackId: int | None = None,
    ) -> None:
        self._newVisitedTileCache = newVisitedTileCache
        self._quickFilterState = quickFilterState
        self._yearFilterState = yearFilterState
        self._trackId = trackId

    def calculate_total_number_of_visited_tiles(
        self,
    ) -> int:
        newVisitedTilesPerTrack = self._newVisitedTileCache.get_new_visited_tiles_per_track_by_user(
            current_user.id
        )

        filteredVisitedTiles = [
            t
            for t in newVisitedTilesPerTrack
            if t.type in self._quickFilterState.get_active_types()
            and t.startTime.year in self._yearFilterState
        ]
        totalNumberOfTiles = 0
        for t in filteredVisitedTiles:
            totalNumberOfTiles += t.numberOfNewTiles

        return totalNumberOfTiles

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

    def get_new_tiles_per_track(self) -> list[NewTilesPerTrack]:
        newVisitedTilesPerTrack = self._newVisitedTileCache.get_new_visited_tiles_per_track_by_user(
            current_user.id
        )

        return [
            t
            for t in newVisitedTilesPerTrack
            if t.type in self._quickFilterState.get_active_types()
            and t.startTime.year in self._yearFilterState
        ]
