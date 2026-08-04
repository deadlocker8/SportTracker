import logging
import time
from datetime import date

from sporttracker import Constants
from sporttracker.quickFilter.QuickFilterStateEntity import get_quick_filter_state_by_user
from sporttracker.tileHunting.MaxSquareCache import MaxSquareCache
from sporttracker.tileHunting.NewVisitedTileCache import NewVisitedTileCache
from sporttracker.user.UserEntity import User
from sporttracker.workout.WorkoutType import WorkoutType

LOGGER = logging.getLogger(Constants.APP_NAME)


def warm_caches(newVisitedTileCache: NewVisitedTileCache, maxSquareCache: MaxSquareCache) -> None:
    users = User.query.order_by(User.id).all()
    if not users:
        return

    LOGGER.info(f'Warming caches for {len(users)} users...')
    start = time.time()

    for user in users:
        combinations: set[tuple[tuple[str, ...], tuple[tuple[date, date], ...] | None]] = set()

        combinations.add((tuple(t.name for t in WorkoutType.get_distance_workout_types()), None))

        quickFilterState = get_quick_filter_state_by_user(user.id)
        activeWorkoutTypes = tuple(t.name for t in quickFilterState.get_active_distance_workout_types())
        effectiveDateRanges = quickFilterState.get_effective_date_ranges()
        combinations.add((activeWorkoutTypes, tuple(effectiveDateRanges) if effectiveDateRanges is not None else None))

        for workoutTypeNames, dateRanges in combinations:
            workoutTypes = [WorkoutType(name) for name in workoutTypeNames]  # type: ignore[call-arg]
            userStart = time.time()
            newVisitedTileCache.get_number_of_new_visited_tiles_per_workout_by_user(
                user.id, workoutTypes, list(dateRanges) if dateRanges is not None else None
            )
            maxSquareCache.get_max_square_tile_positions(
                user.id, workoutTypes, list(dateRanges) if dateRanges is not None else None
            )
            LOGGER.debug(f'Warmed caches for user with ID {user.id} took {(time.time() - userStart):.2f}s')

    LOGGER.info(f'Warming caches for all users DONE (took {(time.time() - start):.2f}s)')
