import logging
import time
from datetime import date, timedelta

from sqlalchemy import and_, or_, false

from sporttracker import Constants
from sporttracker.workout.distance.DistanceWorkoutEntity import DistanceWorkout
from sporttracker.tileHunting.GpxVisitedTileEntity import GpxVisitedTile
from sporttracker.workout.WorkoutType import WorkoutType

LOGGER = logging.getLogger(Constants.APP_NAME)


class MaxSquareCache:
    def __init__(self) -> None:
        self._max_square_tile_positions: dict[str, list[tuple[int, int]]] = {}

    @staticmethod
    def __calculate_cache_key(
        user_id: int, workout_types: list[WorkoutType], date_ranges: list[tuple[date, date]] | None
    ) -> str:
        active_types = '_'.join(sorted([t.name for t in workout_types]))
        if date_ranges is None:
            active_date_ranges = 'NONE'
        else:
            active_date_ranges = '_'.join([f'{date_from}_{date_to}' for date_from, date_to in date_ranges])
        return f'{user_id}_{active_types}_{active_date_ranges}'

    def get_max_square_tile_positions(
        self,
        userId: int,
        workoutTypes: list[WorkoutType],
        dateRanges: list[tuple[date, date]] | None,
    ) -> list[tuple[int, int]]:
        cacheKey = self.__calculate_cache_key(userId, workoutTypes, dateRanges)

        if cacheKey not in self._max_square_tile_positions:
            LOGGER.debug(f'Creating entry in MaxSquareCache with key {cacheKey}...')
            start = time.time()
            self._max_square_tile_positions[cacheKey] = self.__determine_max_square_tile_positions(
                userId, workoutTypes, dateRanges
            )
            LOGGER.debug(f'MaxSquareCache key {cacheKey} took {(time.time() - start):.2f}s')

        return self._max_square_tile_positions[cacheKey]

    def invalidate_cache_entry_by_user(self, userId: int) -> None:
        for key in list(self._max_square_tile_positions.keys()):
            if key.startswith(f'{userId}_'):
                LOGGER.debug(f'Invalidating MaxSquareCache with key with id {key}')
                del self._max_square_tile_positions[key]

    @staticmethod
    def __determine_max_square_tile_positions(
        user_id: int,
        workout_types: list[WorkoutType],
        date_ranges: list[tuple[date, date]] | None,
    ) -> list[tuple[int, int]]:
        query = (
            DistanceWorkout.query.select_from(DistanceWorkout)
            .join(GpxVisitedTile, GpxVisitedTile.workout_id == DistanceWorkout.id)
            .with_entities(GpxVisitedTile.x, GpxVisitedTile.y)
            .filter(DistanceWorkout.user_id == user_id)
            .filter(DistanceWorkout.type.in_(workout_types))
            .distinct()
            .order_by(GpxVisitedTile.x, GpxVisitedTile.y)
        )

        if date_ranges is not None:
            if date_ranges:
                query = query.filter(
                    or_(
                        *(
                            and_(
                                DistanceWorkout.start_time >= date_from,
                                DistanceWorkout.start_time < date_to + timedelta(days=1),
                            )
                            for date_from, date_to in date_ranges
                        )
                    )
                )
            else:
                query = query.filter(false())

        all_visited_tiles = query.all()

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
