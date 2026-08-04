from datetime import datetime

import pytest

from sporttracker.db import db
from sporttracker.gpx.GpxMetadataEntity import GpxMetadata
from sporttracker.tileHunting.CacheWarmer import warm_caches
from sporttracker.tileHunting.GpxVisitedTileEntity import GpxVisitedTile
from sporttracker.user.UserEntity import Language, User, create_user
from sporttracker.workout.distance.DistanceWorkoutEntity import DistanceWorkout
from sporttracker.workout.WorkoutType import WorkoutType
from tests.TestConstants import TEST_PASSWORD, TEST_USERNAME


@pytest.fixture(autouse=True)
def prepare_test_data(app):
    with app.app_context():
        user = create_user(TEST_USERNAME, TEST_PASSWORD, False, Language.ENGLISH, 2026)

        __create_workout_with_visited_tile(user.id, 'Biking 2025', datetime(2025, 6, 15, 10, 0), 35198, 21494)


def __create_workout_with_visited_tile(userId: int, name: str, startTime: datetime, tileX: int, tileY: int) -> None:
    gpxMetadata = GpxMetadata(
        gpx_file_name='test',
        length=0,
        elevation_minimum=None,
        elevation_maximum=None,
        uphill=None,
        downhill=None,
        editor_link=None,
    )
    db.session.add(gpxMetadata)
    db.session.commit()

    workout = DistanceWorkout(
        type=WorkoutType.BIKING,
        name=name,
        start_time=startTime,
        duration=3600,
        distance=10000,
        user_id=userId,
        custom_fields={},
        share_code=None,
        gpx_metadata_id=gpxMetadata.id,
    )
    db.session.add(workout)
    db.session.commit()

    db.session.add(GpxVisitedTile(workout_id=workout.id, x=tileX, y=tileY))
    db.session.commit()


class TestCacheWarmer:
    def test_warm_caches(self, app):
        with app.app_context():
            user = User.query.filter(User.username == TEST_USERNAME).first()
            assert user is not None

            warm_caches(app.config['NEW_VISITED_TILE_CACHE'], app.config['MAX_SQUARE_CACHE'])

            newVisitedTileCache = app.config['NEW_VISITED_TILE_CACHE']
            maxSquareCache = app.config['MAX_SQUARE_CACHE']

            newVisitedTilesPerWorkout = newVisitedTileCache.get_number_of_new_visited_tiles_per_workout_by_user(
                user.id, WorkoutType.get_distance_workout_types(), None
            )
            assert len(newVisitedTilesPerWorkout) == 1
            assert newVisitedTilesPerWorkout[0].numberOfNewTiles == 1

            maxSquareTilePositions = maxSquareCache.get_max_square_tile_positions(
                user.id, WorkoutType.get_distance_workout_types(), None
            )
            assert maxSquareTilePositions == [(35198, 21494)]
