from dataclasses import dataclass

from flask_login import current_user
from sqlalchemy import extract
from sqlalchemy.orm import aliased

from sporttracker.logic.NewVisitedTileCache import NewTilesPerDistanceWorkout, NewVisitedTileCache
from sporttracker.logic.QuickFilterState import QuickFilterState
from sporttracker.logic.model.GpxVisitedTiles import GpxVisitedTile
from sporttracker.logic.model.DistanceWorkout import DistanceWorkout


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
        workoutId: int | None = None,
    ) -> None:
        self._newVisitedTileCache = newVisitedTileCache
        self._quickFilterState = quickFilterState
        self._yearFilterState = yearFilterState
        self._workoutId = workoutId

    def calculate_total_number_of_visited_tiles(
        self,
    ) -> int:
        newVisitedTilesPerWorkout = (
            self._newVisitedTileCache.get_new_visited_tiles_per_workout_by_user(
                current_user.id,
                self._quickFilterState.get_active_distance_workout_types(),
                self._yearFilterState,
            )
        )

        totalNumberOfTiles = 0
        for t in newVisitedTilesPerWorkout:
            totalNumberOfTiles += t.numberOfNewTiles

        return totalNumberOfTiles

    def determine_tile_colors_of_workouts_that_visit_tiles(
        self, min_x: int, max_x: int, min_y: int, max_y: int, user_id: int
    ) -> list[TileColorPosition]:
        if self._workoutId is None:
            return self.__determine_tile_colors_of_all_workouts_that_visit_tiles(
                min_x, max_x, min_y, max_y, user_id
            )

        return self.__determine_tile_colors_of_single_workout(
            min_x, max_x, min_y, max_y, self._workoutId
        )

    def __determine_tile_colors_of_all_workouts_that_visit_tiles(
        self, min_x: int, max_x: int, min_y: int, max_y: int, user_id: int
    ) -> list[TileColorPosition]:
        distanceWorkoutAlias = aliased(DistanceWorkout)
        gpxVisitedTileAlias = aliased(GpxVisitedTile)

        rows = (
            distanceWorkoutAlias.query.select_from(distanceWorkoutAlias)
            .join(gpxVisitedTileAlias, gpxVisitedTileAlias.workout_id == distanceWorkoutAlias.id)
            .with_entities(distanceWorkoutAlias.type, gpxVisitedTileAlias.x, gpxVisitedTileAlias.y)
            .filter(distanceWorkoutAlias.user_id == user_id)
            .filter(
                distanceWorkoutAlias.type.in_(
                    self._quickFilterState.get_active_distance_workout_types()
                )
            )
            .filter(extract('year', distanceWorkoutAlias.start_time).in_(self._yearFilterState))
            .filter(gpxVisitedTileAlias.x >= min_x)
            .filter(gpxVisitedTileAlias.x <= max_x)
            .filter(gpxVisitedTileAlias.y >= min_y)
            .filter(gpxVisitedTileAlias.y <= max_y)
            .group_by(gpxVisitedTileAlias.x, gpxVisitedTileAlias.y, distanceWorkoutAlias.type)
            .all()
        )

        return [TileColorPosition(r[0].tile_color, r[1], r[2]) for r in rows]

    def __determine_tile_colors_of_single_workout(
        self, min_x: int, max_x: int, min_y: int, max_y: int, workoutId: int
    ) -> list[TileColorPosition]:
        distanceWorkoutAlias = aliased(DistanceWorkout)
        gpxVisitedTileAlias = aliased(GpxVisitedTile)

        rows = (
            distanceWorkoutAlias.query.select_from(distanceWorkoutAlias)
            .join(gpxVisitedTileAlias, gpxVisitedTileAlias.workout_id == distanceWorkoutAlias.id)
            .with_entities(distanceWorkoutAlias.type, gpxVisitedTileAlias.x, gpxVisitedTileAlias.y)
            .filter(distanceWorkoutAlias.user_id == current_user.id)
            .filter(distanceWorkoutAlias.id == workoutId)
            .filter(gpxVisitedTileAlias.x >= min_x)
            .filter(gpxVisitedTileAlias.x <= max_x)
            .filter(gpxVisitedTileAlias.y >= min_y)
            .filter(gpxVisitedTileAlias.y <= max_y)
            .group_by(gpxVisitedTileAlias.x, gpxVisitedTileAlias.y, distanceWorkoutAlias.type)
            .all()
        )

        return [TileColorPosition(r[0].tile_color, r[1], r[2]) for r in rows]

    def get_new_tiles_per_workout(self) -> list[NewTilesPerDistanceWorkout]:
        return self._newVisitedTileCache.get_new_visited_tiles_per_workout_by_user(
            current_user.id,
            self._quickFilterState.get_active_distance_workout_types(),
            self._yearFilterState,
        )
