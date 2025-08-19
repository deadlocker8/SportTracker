import os
from datetime import datetime

from sporttracker.logic.FitSessionParser import FitSessionParser
from sporttracker.workout.WorkoutType import WorkoutType
from tests.TestConstants import ROOT_DIRECTORY


class TestFitSessionParser:
    def test_parse(self):
        dataDirectory = os.path.join(ROOT_DIRECTORY, 'sporttracker', 'dummyData')
        fitFilePath = os.path.join(dataDirectory, 'fitTrack_1.fit')

        fitSession = FitSessionParser().parse(fitFilePath)
        assert fitSession is not None
        assert fitSession.file_name == 'fitTrack_1'
        assert fitSession.start_time == datetime(
            year=2024, month=9, day=20, hour=16, minute=30, second=6, microsecond=0
        )
        assert fitSession.duration == 5102
        assert fitSession.distance == 35390
        assert fitSession.total_ascent == 319
        assert fitSession.average_heart_rate is None
        assert fitSession.workout_type == WorkoutType.BIKING
