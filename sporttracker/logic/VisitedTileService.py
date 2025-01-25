from dataclasses import dataclass

from flask_login import current_user
from sqlalchemy import extract
from sqlalchemy.orm import aliased

from sporttracker.logic.NewVisitedTileCache import NewTilesPerDistanceSport, NewVisitedTileCache
from sporttracker.logic.QuickFilterState import QuickFilterState
from sporttracker.logic.model.GpxVisitedTiles import GpxVisitedTile
from sporttracker.logic.model.DistanceSport import DistanceSport


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
        sportId: int | None = None,
    ) -> None:
        self._newVisitedTileCache = newVisitedTileCache
        self._quickFilterState = quickFilterState
        self._yearFilterState = yearFilterState
        self._sportId = sportId

    def calculate_total_number_of_visited_tiles(
        self,
    ) -> int:
        newVisitedTilesPerTrack = self._newVisitedTileCache.get_new_visited_tiles_per_track_by_user(
            current_user.id,
            self._quickFilterState.get_active_distance_sport_types(),
            self._yearFilterState,
        )

        totalNumberOfTiles = 0
        for t in newVisitedTilesPerTrack:
            totalNumberOfTiles += t.numberOfNewTiles

        return totalNumberOfTiles

    def determine_tile_colors_of_tracks_that_visit_tiles(
        self, min_x: int, max_x: int, min_y: int, max_y: int, user_id: int
    ) -> list[TileColorPosition]:
        if self._sportId is None:
            return self.__determine_tile_colors_of_all_tracks_that_visit_tiles(
                min_x, max_x, min_y, max_y, user_id
            )

        return self.__determine_tile_colors_of_single_track(
            min_x, max_x, min_y, max_y, self._sportId
        )

    def __determine_tile_colors_of_all_tracks_that_visit_tiles(
        self, min_x: int, max_x: int, min_y: int, max_y: int, user_id: int
    ) -> list[TileColorPosition]:
        distanceSportAlias = aliased(DistanceSport)
        gpxVisitedTileAlias = aliased(GpxVisitedTile)

        rows = (
            distanceSportAlias.query.select_from(distanceSportAlias)
            .join(gpxVisitedTileAlias, gpxVisitedTileAlias.sport_id == distanceSportAlias.id)
            .with_entities(distanceSportAlias.type, gpxVisitedTileAlias.x, gpxVisitedTileAlias.y)
            .filter(distanceSportAlias.user_id == user_id)
            .filter(
                distanceSportAlias.type.in_(
                    self._quickFilterState.get_active_distance_sport_types()
                )
            )
            .filter(extract('year', distanceSportAlias.start_time).in_(self._yearFilterState))
            .filter(gpxVisitedTileAlias.x >= min_x)
            .filter(gpxVisitedTileAlias.x <= max_x)
            .filter(gpxVisitedTileAlias.y >= min_y)
            .filter(gpxVisitedTileAlias.y <= max_y)
            .group_by(gpxVisitedTileAlias.x, gpxVisitedTileAlias.y, distanceSportAlias.type)
            .all()
        )

        return [TileColorPosition(r[0].tile_color, r[1], r[2]) for r in rows]

    def __determine_tile_colors_of_single_track(
        self, min_x: int, max_x: int, min_y: int, max_y: int, sportId: int
    ) -> list[TileColorPosition]:
        distanceSportAlias = aliased(DistanceSport)
        gpxVisitedTileAlias = aliased(GpxVisitedTile)

        rows = (
            distanceSportAlias.query.select_from(distanceSportAlias)
            .join(gpxVisitedTileAlias, gpxVisitedTileAlias.sport_id == distanceSportAlias.id)
            .with_entities(distanceSportAlias.type, gpxVisitedTileAlias.x, gpxVisitedTileAlias.y)
            .filter(distanceSportAlias.user_id == current_user.id)
            .filter(distanceSportAlias.id == sportId)
            .filter(gpxVisitedTileAlias.x >= min_x)
            .filter(gpxVisitedTileAlias.x <= max_x)
            .filter(gpxVisitedTileAlias.y >= min_y)
            .filter(gpxVisitedTileAlias.y <= max_y)
            .group_by(gpxVisitedTileAlias.x, gpxVisitedTileAlias.y, distanceSportAlias.type)
            .all()
        )

        return [TileColorPosition(r[0].tile_color, r[1], r[2]) for r in rows]

    def get_new_tiles_per_track(self) -> list[NewTilesPerDistanceSport]:
        return self._newVisitedTileCache.get_new_visited_tiles_per_track_by_user(
            current_user.id,
            self._quickFilterState.get_active_distance_sport_types(),
            self._yearFilterState,
        )
