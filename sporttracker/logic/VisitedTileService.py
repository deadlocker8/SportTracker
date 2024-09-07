from flask_login import current_user
from sqlalchemy import extract
from sqlalchemy.orm import aliased

from sporttracker.logic.QuickFilterState import QuickFilterState
from sporttracker.logic.model.GpxVisitedTiles import GpxVisitedTile
from sporttracker.logic.model.Track import Track


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

    def determine_tile_colors_of_tracks_that_visit_tile(self, x: int, y: int) -> list[str]:
        if self._trackId is None:
            return self.__determine_tile_colors_of_all_tracks_that_visit_tile(x, y)

        return self.__determine_tile_colors_of_single_track(x, y, self._trackId)

    def __determine_tile_colors_of_all_tracks_that_visit_tile(self, x: int, y: int) -> list[str]:
        trackAlias = aliased(Track)
        gpxVisitedTileAlias = aliased(GpxVisitedTile)

        rows = (
            trackAlias.query.select_from(trackAlias)
            .join(gpxVisitedTileAlias, gpxVisitedTileAlias.track_id == trackAlias.id)
            .filter(trackAlias.user_id == current_user.id)
            .filter(trackAlias.type.in_(self._quickFilterState.get_active_types()))
            .filter(extract('year', trackAlias.startTime).in_(self._yearFilterState))
            .filter(gpxVisitedTileAlias.x == x)
            .filter(gpxVisitedTileAlias.y == y)
            .with_entities(trackAlias.type)
            .all()
        )
        return [row[0].tile_color for row in rows]

    def __determine_tile_colors_of_single_track(self, x: int, y: int, trackId: int) -> list[str]:
        trackAlias = aliased(Track)
        gpxVisitedTileAlias = aliased(GpxVisitedTile)

        rows = (
            trackAlias.query.select_from(trackAlias)
            .join(gpxVisitedTileAlias, gpxVisitedTileAlias.track_id == trackAlias.id)
            .filter(trackAlias.user_id == current_user.id)
            .filter(trackAlias.id == trackId)
            .filter(gpxVisitedTileAlias.x == x)
            .filter(gpxVisitedTileAlias.y == y)
            .with_entities(trackAlias.type)
            .all()
        )

        return [row[0].tile_color for row in rows]
