import math
from dataclasses import dataclass

from flask_login import current_user
from sqlalchemy import extract, text, func, or_
from sqlalchemy.orm import aliased

from sporttracker.gpx.GpxService import VisitedTile
from sporttracker.tileHunting.GpxPlannedTileEntity import GpxPlannedTile
from sporttracker.plannedTour.PlannedTourEntity import PlannedTour
from sporttracker.tileHunting.MaxSquareCache import MaxSquareCache
from sporttracker.tileHunting.NewVisitedTileCache import NewVisitedTileCache, NewTilesPerDistanceWorkout
from sporttracker.workout.WorkoutType import WorkoutType
from sporttracker.quickFilter.QuickFilterStateEntity import QuickFilterState
from sporttracker.tileHunting.TileHuntingFilterStateEntity import TileHuntingFilterState
from sporttracker.workout.distance.DistanceWorkoutEntity import DistanceWorkout
from sporttracker.tileHunting.GpxVisitedTileEntity import GpxVisitedTile
from sporttracker.db import db
from sporttracker.workout.distance.DistanceWorkoutService import DistanceWorkoutService


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
        tileHuntingFilterState: TileHuntingFilterState,
        distanceWorkoutService: DistanceWorkoutService,
        workoutId: int | None = None,
    ) -> None:
        self._newVisitedTileCache = newVisitedTileCache
        self._maxSquareCache = maxSquareCache
        self._quickFilterState = quickFilterState
        self._tileHuntingFilterState = tileHuntingFilterState
        self._distanceWorkoutService = distanceWorkoutService
        self._workoutId = workoutId

    def calculate_total_number_of_visited_tiles(
        self,
    ) -> int:
        newVisitedTilesPerWorkout = self._newVisitedTileCache.get_number_of_new_visited_tiles_per_workout_by_user(
            current_user.id,
            self._quickFilterState.get_active_distance_workout_types(),
            self._quickFilterState.years,
        )

        totalNumberOfTiles = 0
        for t in newVisitedTilesPerWorkout:
            totalNumberOfTiles += t.numberOfNewTiles

        return totalNumberOfTiles

    def determine_tile_colors_of_workouts_that_visit_tiles(
        self, min_x: int, max_x: int, min_y: int, max_y: int, user_id: int
    ) -> list[TileColorPosition]:
        if self._workoutId is None:
            return self.__determine_tile_colors_of_all_workouts_that_visit_tiles(min_x, max_x, min_y, max_y, user_id)

        return self.__determine_tile_colors_of_single_workout(
            min_x,
            max_x,
            min_y,
            max_y,
            self._workoutId,
            self._tileHuntingFilterState.is_only_highlight_new_tiles_active,  # type: ignore[arg-type]
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
            .filter(distanceWorkoutAlias.type.in_(self._quickFilterState.get_active_distance_workout_types()))
            .filter(extract('year', distanceWorkoutAlias.start_time).in_(self._quickFilterState.years))
            .filter(gpxVisitedTileAlias.x >= min_x)
            .filter(gpxVisitedTileAlias.x <= max_x)
            .filter(gpxVisitedTileAlias.y >= min_y)
            .filter(gpxVisitedTileAlias.y <= max_y)
            .group_by(gpxVisitedTileAlias.x, gpxVisitedTileAlias.y, distanceWorkoutAlias.type)
            .all()
        )

        return [TileColorPosition(r[0].tile_color, r[1], r[2]) for r in rows]

    def determine_planned_tiles(
        self, min_x: int, max_x: int, min_y: int, max_y: int, user_id: int
    ) -> list[VisitedTile]:
        if self._workoutId is not None:
            return []

        if not self._tileHuntingFilterState.is_show_planned_tiles_active:  # type: ignore[arg-type]
            return []

        plannedTourAlias = aliased(PlannedTour)
        gpxPlannedTileAlias = aliased(GpxPlannedTile)

        rows = (
            plannedTourAlias.query.select_from(plannedTourAlias)
            .join(gpxPlannedTileAlias, gpxPlannedTileAlias.planned_tour_id == plannedTourAlias.id)
            .with_entities(gpxPlannedTileAlias.x, gpxPlannedTileAlias.y)
            .filter(
                or_(
                    plannedTourAlias.user_id == user_id,
                    plannedTourAlias.shared_users.any(id=user_id),
                )
            )
            .filter(plannedTourAlias.type.in_(self._quickFilterState.get_active_distance_workout_types()))
            .filter(gpxPlannedTileAlias.x >= min_x)
            .filter(gpxPlannedTileAlias.x <= max_x)
            .filter(gpxPlannedTileAlias.y >= min_y)
            .filter(gpxPlannedTileAlias.y <= max_y)
            .group_by(gpxPlannedTileAlias.x, gpxPlannedTileAlias.y)
            .all()
        )

        return [VisitedTile(r[0], r[1]) for r in rows]

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
            .filter(distanceWorkoutAlias.type.in_(self._quickFilterState.get_active_distance_workout_types()))
            .filter(extract('year', distanceWorkoutAlias.start_time).in_(self._quickFilterState.years))
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

        workout = self._distanceWorkoutService.get_distance_workout_by_id(workoutId, current_user.id)
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
            self._quickFilterState.years,
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
            self._quickFilterState.years,
        )

    def get_max_square_size(self) -> int:
        maxSquareTilePositions = self.get_max_square_tile_positions()
        if not maxSquareTilePositions:
            return 0

        return int(math.sqrt(len(maxSquareTilePositions)))

    def get_number_of_new_tiles_per_workout_type_per_year(
        self, min_year: int, max_year: int, workout_types: list[WorkoutType]
    ) -> dict[WorkoutType, dict[int, int]]:
        numberOfVisitedTilesPerWorkout = self._newVisitedTileCache.get_number_of_new_visited_tiles_per_workout_by_user(
            current_user.id,
            workout_types,
            self._quickFilterState.years,
        )

        result = {}
        for workoutType in workout_types:
            numberOfNewTilesPerYear = {}
            for currentYear in range(min_year, max_year + 1):
                numberOfNewTiles = 0
                for entry in numberOfVisitedTilesPerWorkout:
                    if entry.type != workoutType:
                        continue

                    if entry.startTime.year != currentYear:
                        continue

                    numberOfNewTiles = numberOfNewTiles + entry.numberOfNewTiles

                numberOfNewTilesPerYear[currentYear] = numberOfNewTiles

            result[workoutType] = numberOfNewTilesPerYear

        return result
