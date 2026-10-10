import logging
import time
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import and_, false, or_

from sporttracker import Constants
from sporttracker.metrics.LoadStatisticsCollector import LoadStatisticsCollector
from sporttracker.tileHunting.GpxVisitedTileEntity import GpxVisitedTile
from sporttracker.workout.distance.DistanceWorkoutEntity import DistanceWorkout
from sporttracker.workout.WorkoutType import WorkoutType

LOGGER = logging.getLogger(Constants.APP_NAME)


@dataclass
class VisitedTilesEntry:
    visited_tiles: list[tuple[int, int]]
    max_square_tile_positions: list[tuple[int, int]] | None = None
    max_cluster_tile_positions: list[tuple[int, int]] | None = None


class VisitedTileCache:
    def __init__(self, loadStatisticsCollector: LoadStatisticsCollector) -> None:
        self._loadStatisticsCollector = loadStatisticsCollector
        self._entries: dict[str, VisitedTilesEntry] = {}

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
        entry = self.__get_entry(userId, workoutTypes, dateRanges)
        if entry.max_square_tile_positions is None:
            entry.max_square_tile_positions = VisitedTileCache._calculate_max_square(entry.visited_tiles)

        return entry.max_square_tile_positions

    def get_max_cluster_tile_positions(
        self,
        userId: int,
        workoutTypes: list[WorkoutType],
        dateRanges: list[tuple[date, date]] | None,
    ) -> list[tuple[int, int]]:
        entry = self.__get_entry(userId, workoutTypes, dateRanges)
        if entry.max_cluster_tile_positions is None:
            entry.max_cluster_tile_positions = VisitedTileCache._calculate_max_cluster(entry.visited_tiles)

        return entry.max_cluster_tile_positions

    def invalidate_cache_entry_by_user(self, userId: int) -> None:
        for key in list(self._entries.keys()):
            if key.startswith(f'{userId}_'):
                LOGGER.debug(f'Invalidating VisitedTileCache with key with id {key}')
                del self._entries[key]

        self._loadStatisticsCollector.invalidate_cache_entry_by_user(type(self).__name__, userId)

    def __get_entry(
        self,
        userId: int,
        workoutTypes: list[WorkoutType],
        dateRanges: list[tuple[date, date]] | None,
    ) -> VisitedTilesEntry:
        cacheKey = self.__calculate_cache_key(userId, workoutTypes, dateRanges)

        if cacheKey not in self._entries:
            LOGGER.debug(f'Creating entry in VisitedTileCache with key {cacheKey}...')
            start = time.time()
            self._entries[cacheKey] = VisitedTilesEntry(
                VisitedTileCache.__determine_visited_tiles(userId, workoutTypes, dateRanges)
            )
            duration = time.time() - start
            LOGGER.debug(f'VisitedTileCache key {cacheKey} took {duration:.2f}s')
            self._loadStatisticsCollector.record_cache_calculation(
                type(self).__name__, userId, workoutTypes, dateRanges, duration
            )

        return self._entries[cacheKey]

    @staticmethod
    def __determine_visited_tiles(
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

        return [(row[0], row[1]) for row in all_visited_tiles]

    @staticmethod
    def _calculate_max_square(tiles: list[tuple[int, int]]) -> list[tuple[int, int]]:
        max_size = 0
        square_tile_positions = []

        for x, y in tiles:
            # Try squares of increasing size starting from 1
            for size in range(1, min(len(tiles), max(x, y)) + 2):
                all_positions_in_square = [(x + dx, y + dy) for dx in range(size) for dy in range(size)]
                if not all(t in tiles for t in all_positions_in_square):
                    break

                if size > max_size:
                    max_size = size
                    square_tile_positions = all_positions_in_square

        return square_tile_positions

    @staticmethod
    def _calculate_max_cluster(tiles: list[tuple[int, int]]) -> list[tuple[int, int]]:
        positions = set(tiles)
        biggest_cluster: list[tuple[int, int]] = []
        visited: set[tuple[int, int]] = set()

        for tile in tiles:
            if tile in visited:
                continue

            stack = [tile]
            visited.add(tile)
            cluster: list[tuple[int, int]] = []

            while stack:
                current = stack.pop()
                cluster.append(current)

                for x, y in (
                    (current[0] - 1, current[1]),
                    (current[0] + 1, current[1]),
                    (current[0], current[1] - 1),
                    (current[0], current[1] + 1),
                ):
                    neighbor = (x, y)
                    if neighbor in positions and neighbor not in visited:
                        visited.add(neighbor)
                        stack.append(neighbor)

            if len(cluster) > len(biggest_cluster):
                biggest_cluster = cluster

        return biggest_cluster
