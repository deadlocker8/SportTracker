import os
from datetime import date, datetime

import pytest

from sporttracker.db import db
from sporttracker.gpx.GpxMetadataEntity import GpxMetadata
from sporttracker.longDistanceTour.LongDistanceTourEntity import LongDistanceTour
from sporttracker.metrics.LoadStatisticsCollector import LoadStatisticsCollector
from sporttracker.plannedTour.PlannedTourEntity import PlannedTour
from sporttracker.plannedTour.TravelDirection import TravelDirection
from sporttracker.plannedTour.TravelType import TravelType
from sporttracker.serverStatistics.ServerStatisticsService import ServerStatisticsService
from sporttracker.user.UserEntity import Language, User, create_user
from sporttracker.workout.distance.DistanceWorkoutEntity import DistanceWorkout
from sporttracker.workout.fitness.FitnessWorkoutEntity import FitnessWorkout
from sporttracker.workout.fitness.FitnessWorkoutType import FitnessWorkoutType
from sporttracker.workout.WorkoutType import WorkoutType


@pytest.fixture(autouse=True)
def prepare_test_data(app, tmp_path):
    dataPath = os.path.join(str(tmp_path), 'data')
    with app.app_context():
        aliceUserId = create_user('alice', 'topSecret0815', False, Language.ENGLISH, 2026).id
        bobUserId = create_user('bob', 'topSecret0815', False, Language.ENGLISH, 2026).id

        trackAMetadata = GpxMetadata(gpx_file_name='trackA', length=100.0)
        trackBMetadata = GpxMetadata(gpx_file_name='trackB', length=200.0)
        db.session.add(trackAMetadata)
        db.session.add(trackBMetadata)
        db.session.commit()

        db.session.add(
            DistanceWorkout(
                name='Run with track',
                start_time=datetime(2024, 1, 1, 15, 30),
                duration=3600,
                distance=10000,
                type=WorkoutType.RUNNING,
                user_id=aliceUserId,
                gpx_metadata_id=trackAMetadata.id,
            )
        )
        db.session.add(
            DistanceWorkout(
                name='Run without track',
                start_time=datetime(2024, 1, 2, 15, 30),
                duration=1800,
                distance=5000,
                type=WorkoutType.RUNNING,
                user_id=aliceUserId,
                gpx_metadata_id=None,
            )
        )
        db.session.add(
            FitnessWorkout(
                name='Gym',
                start_time=datetime(2024, 1, 3, 15, 30),
                duration=3600,
                fitness_workout_type=FitnessWorkoutType.DURATION_BASED,
                user_id=bobUserId,
            )
        )

        db.session.add(
            PlannedTour(
                id=1,
                type=WorkoutType.BIKING,
                name='Planned tour with preview',
                creation_date=datetime.now(),
                last_edit_date=datetime.now(),
                last_edit_user_id=aliceUserId,
                gpx_metadata_id=trackBMetadata.id,
                user_id=aliceUserId,
                shared_users=[],
                arrival_method=TravelType.TRAIN,
                departure_method=TravelType.NONE,
                direction=TravelDirection.SINGLE,
                share_code=None,
            )
        )
        db.session.add(
            PlannedTour(
                id=2,
                type=WorkoutType.BIKING,
                name='Shared planned tour',
                creation_date=datetime.now(),
                last_edit_date=datetime.now(),
                last_edit_user_id=bobUserId,
                gpx_metadata_id=trackAMetadata.id,
                user_id=bobUserId,
                shared_users=[],
                arrival_method=TravelType.TRAIN,
                departure_method=TravelType.NONE,
                direction=TravelDirection.SINGLE,
                share_code=None,
            )
        )

        db.session.add(
            LongDistanceTour(
                id=1,
                type=WorkoutType.BIKING,
                name='Long distance tour',
                creation_date=datetime.now(),
                last_edit_date=datetime.now(),
                last_edit_user_id=aliceUserId,
                user_id=aliceUserId,
                shared_users=[],
                linked_planned_tours=[],
            )
        )
        db.session.commit()

        __write_file(os.path.join(dataPath, 'trackA', 'trackA.gpx.zip'), 100)
        __write_file(os.path.join(dataPath, 'trackA', 'trackA.fit'), 40)
        __write_file(os.path.join(dataPath, 'trackB', 'trackB.gpx.zip'), 200)
        __write_file(os.path.join(dataPath, 'trackB', 'trackB.jpg'), 50)
        __write_file(os.path.join(dataPath, 'long_distance_tour_1', 'long_distance_tour_1.jpg'), 60)

    return dataPath


def __write_file(filePath: str, size: int) -> None:
    directory = os.path.dirname(filePath)
    os.makedirs(directory, exist_ok=True)
    with open(filePath, 'wb') as f:
        f.write(b'x' * size)


class TestServerStatisticsService:
    def test_get_global_statistics(self, app, prepare_test_data):
        with app.app_context():
            statistics = ServerStatisticsService(prepare_test_data, LoadStatisticsCollector()).get_global_statistics()

            assert statistics.numberOfUsers == User.query.count()
            assert statistics.numberOfWorkouts == 3
            assert statistics.numberOfGpxTracks == 2
            assert statistics.totalGpxFileSize == 340
            assert statistics.numberOfPreviewImages == 2

    def test_get_user_statistics(self, app, prepare_test_data):
        with app.app_context():
            userStatistics = ServerStatisticsService(prepare_test_data, LoadStatisticsCollector()).get_user_statistics()

            statisticsByUsername = {s.username: s for s in userStatistics}

            assert len(userStatistics) == User.query.count()

            alice = statisticsByUsername['alice']
            assert alice.numberOfWorkouts == 2
            assert alice.numberOfGpxTracks == 2
            assert alice.totalGpxFileSize == 340
            assert alice.numberOfPreviewImages == 2

            bob = statisticsByUsername['bob']
            assert bob.numberOfWorkouts == 1
            assert bob.numberOfGpxTracks == 1
            assert bob.totalGpxFileSize == 140
            assert bob.numberOfPreviewImages == 0

    def test_get_cache_calculation_statistics(self, app, prepare_test_data):
        with app.app_context():
            alice = User.query.filter(User.username == 'alice').first()

            collector = LoadStatisticsCollector()
            collector.record_cache_calculation(
                'NewVisitedTileCache',
                alice.id,
                [WorkoutType.RUNNING],
                [(date(2024, 1, 1), date(2024, 1, 31))],
                1.234,
            )

            statistics = ServerStatisticsService(prepare_test_data, collector).get_cache_calculation_statistics()

            assert len(statistics) == 1
            assert statistics[0].cacheName == 'NewVisitedTileCache'
            assert statistics[0].username == 'alice'
            assert statistics[0].durationSeconds == 1.234
