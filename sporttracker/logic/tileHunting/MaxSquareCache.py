import logging

from sqlalchemy import extract

from sporttracker.logic import Constants
from sporttracker.logic.model.DistanceWorkout import DistanceWorkout
from sporttracker.logic.model.GpxVisitedTile import GpxVisitedTile
from sporttracker.logic.model.WorkoutType import WorkoutType

LOGGER = logging.getLogger(Constants.APP_NAME)


class MaxSquareCache:
    def __init__(self) -> None:
        self._max_square_tile_positions: dict[str, list[tuple[int, int]]] = {}

    @staticmethod
    def __calculate_cache_key(user_id: int, workout_types: list[WorkoutType], years: list[int]) -> str:
        active_types = '_'.join(sorted([t.name for t in workout_types]))
        active_years = '_'.join(sorted([str(y) for y in years]))
        return f'{user_id}_{active_types}_{active_years}'

    def get_max_square_tile_positions(
        self, userId: int, workoutTypes: list[WorkoutType], years: list[int]
    ) -> list[tuple[int, int]]:
        cacheKey = self.__calculate_cache_key(userId, workoutTypes, years)

        if cacheKey not in self._max_square_tile_positions:
            LOGGER.debug(f'Creating entry in MaxSquareCache with key {cacheKey}')
            self._max_square_tile_positions[cacheKey] = self.__determine_max_square_tile_positions(
                userId, workoutTypes, years
            )

        return self._max_square_tile_positions[cacheKey]

    def invalidate_cache_entry_by_user(self, userId: int) -> None:
        for key in list(self._max_square_tile_positions.keys()):
            if key.startswith(f'{userId}_'):
                LOGGER.debug(f'Invalidating MaxSquareCache with key with id {key}')
                del self._max_square_tile_positions[key]

    @staticmethod
    def __determine_max_square_tile_positions(
        user_id: int, workout_types: list[WorkoutType], years: list[int]
    ) -> list[tuple[int, int]]:
        all_visited_tiles = (
            DistanceWorkout.query.select_from(DistanceWorkout)
            .join(GpxVisitedTile, GpxVisitedTile.workout_id == DistanceWorkout.id)
            .with_entities(GpxVisitedTile.x, GpxVisitedTile.y)
            .filter(DistanceWorkout.user_id == user_id)
            .filter(DistanceWorkout.type.in_(workout_types))
            .filter(extract('year', DistanceWorkout.start_time).in_(years))
            .distinct()
            .order_by(GpxVisitedTile.x, GpxVisitedTile.y)
            .all()
        )

        return MaxSquareCache._calculate_max_square([(row[0], row[1]) for row in all_visited_tiles])

    @staticmethod
    def _calculate_max_square(tiles: list[tuple[int, int]]) -> list[tuple[int, int]]:
        max_size = 0
        square_tile_positions = []

        for x, y in tiles:
            # Try squares of increasing size starting from 1
            for size in range(1, min(len(tiles), max(x, y)) + 2):
                all_positions_in_square = [(x + dx, y + dy) for dx in range(size) for dy in range(size)]
                if not all([t in tiles for t in all_positions_in_square]):
                    break

                if size > max_size:
                    max_size = size
                    square_tile_positions = all_positions_in_square

        return square_tile_positions
