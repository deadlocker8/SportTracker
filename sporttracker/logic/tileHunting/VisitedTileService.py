import math
from dataclasses import dataclass

from flask_login import current_user
from sqlalchemy import extract, text, func
from sqlalchemy.orm import aliased

from sporttracker.logic.tileHunting.MaxSquareCache import MaxSquareCache
from sporttracker.logic.tileHunting.NewVisitedTileCache import (
    NewTilesPerDistanceWorkout,
    NewVisitedTileCache,
)
from sporttracker.logic.QuickFilterState import QuickFilterState
from sporttracker.logic.model.DistanceWorkout import DistanceWorkout
from sporttracker.logic.model.GpxVisitedTiles import GpxVisitedTile
from sporttracker.logic.model.db import db
from sporttracker.logic.service.DistanceWorkoutService import DistanceWorkoutService


@dataclass
class TileColorPosition:
    tile_color: str
    x: int
    y: int


@dataclass
class TileCountPosition:
    count: int
    x: int
    y: int


class VisitedTileService:
    COLOR_NOT_NEW = '#00000055'

    def __init__(
        self,
        newVisitedTileCache: NewVisitedTileCache,
        maxSquareCache: MaxSquareCache,
        quickFilterState: QuickFilterState,
        yearFilterState: list[int],
        distanceWorkoutService: DistanceWorkoutService,
        workoutId: int | None = None,
        onlyHighlightNewTiles: bool = False,
    ) -> None:
        self._newVisitedTileCache = newVisitedTileCache
        self._maxSquareCache = maxSquareCache
        self._quickFilterState = quickFilterState
        self._yearFilterState = yearFilterState
        self._distanceWorkoutService = distanceWorkoutService
        self._workoutId = workoutId
        self._onlyHighlightNewTiles = onlyHighlightNewTiles

    def calculate_total_number_of_visited_tiles(
        self,
    ) -> int:
        newVisitedTilesPerWorkout = (
            self._newVisitedTileCache.get_number_of_new_visited_tiles_per_workout_by_user(
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
            min_x, max_x, min_y, max_y, self._workoutId, self._onlyHighlightNewTiles
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

    def determine_number_of_visits(
        self, min_x: int, max_x: int, min_y: int, max_y: int, user_id: int
    ) -> list[TileCountPosition]:
        distanceWorkoutAlias = aliased(DistanceWorkout)
        gpxVisitedTileAlias = aliased(GpxVisitedTile)

        rows = (
            distanceWorkoutAlias.query.select_from(distanceWorkoutAlias)
            .join(gpxVisitedTileAlias, gpxVisitedTileAlias.workout_id == distanceWorkoutAlias.id)
            .with_entities(func.count(), gpxVisitedTileAlias.x, gpxVisitedTileAlias.y)
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
            .group_by(gpxVisitedTileAlias.x, gpxVisitedTileAlias.y)
            .all()
        )

        return [TileCountPosition(r[0], r[1], r[2]) for r in rows]

    def __determine_tile_colors_of_single_workout(
        self,
        min_x: int,
        max_x: int,
        min_y: int,
        max_y: int,
        workoutId: int,
        onlyHighlightNewTiles: bool,
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

        workout = self._distanceWorkoutService.get_distance_workout_by_id(
            workoutId, current_user.id
        )
        newVisitedTiles = []
        if workout is not None:
            newVisitedTiles = VisitedTileService.__get_new_visited_tiles_by_workout(workout)

        result = []
        for row in rows:
            if onlyHighlightNewTiles:
                tileColor = VisitedTileService.COLOR_NOT_NEW
                if (row[1], row[2]) in newVisitedTiles:
                    tileColor = row[0].tile_color
            else:
                tileColor = row[0].tile_color

            result.append(TileColorPosition(tileColor, row[1], row[2]))

        return result

    def get_number_of_new_tiles_per_workout(self) -> list[NewTilesPerDistanceWorkout]:
        return self._newVisitedTileCache.get_number_of_new_visited_tiles_per_workout_by_user(
            current_user.id,
            self._quickFilterState.get_active_distance_workout_types(),
            self._yearFilterState,
        )

    @staticmethod
    def __get_new_visited_tiles_by_workout(workout: DistanceWorkout) -> list[tuple[int, int]]:
        rows = db.session.execute(
            text(f"""SELECT *
            FROM gpx_visited_tile
            WHERE gpx_visited_tile."workout_id" = {workout.id}
              AND NOT EXISTS (SELECT
                              FROM distance_workout AS prev
                                       join gpx_visited_tile AS visitied ON prev."id" = visitied."workout_id"
                                       JOIN workout w_inner ON prev."id" = w_inner."id"
                              WHERE w_inner."start_time" < '{workout.start_time}'
                                AND w_inner."user_id" = {workout.user.id}
                                AND gpx_visited_tile."x" = visitied."x"
                                AND gpx_visited_tile."y" = visitied."y")""")
        ).fetchall()

        return [(row[1], row[2]) for row in rows]

    def get_max_square_tile_positions(self) -> list[tuple[int, int]]:
        return self._maxSquareCache.get_max_square_tile_positions(
            current_user.id,
            self._quickFilterState.get_active_distance_workout_types(),
            self._yearFilterState,
        )

    def get_max_square_size(self) -> int:
        maxSquareTilePositions = self.get_max_square_tile_positions()
        if not maxSquareTilePositions:
            return 0

        return int(math.sqrt(len(maxSquareTilePositions)))
