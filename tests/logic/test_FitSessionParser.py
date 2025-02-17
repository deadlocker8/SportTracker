import os
from datetime import datetime

from sporttracker.logic.FitSessionParser import FitSessionParser
from sporttracker.logic.model.WorkoutType import WorkoutType


class TestFitSessionParser:
    def test_parse(self):
        currentDirectory = os.path.abspath(os.path.dirname(__file__))
        rootDirectory = os.path.dirname(os.path.dirname(currentDirectory))
        dataDirectory = os.path.join(rootDirectory, 'sporttracker', 'dummyData')
        fitFilePath = os.path.join(dataDirectory, 'fitTrack_1.fit')

        fitSession = FitSessionParser().parse(fitFilePath)
        assert fitSession is not None
        assert fitSession.file_name == 'fitTrack_1'
        assert fitSession.start_time == datetime(
            year=2024, month=9, day=20, hour=18, minute=30, second=6, microsecond=0
        )
        assert fitSession.duration == 5102
        assert fitSession.distance == 35390
        assert fitSession.total_ascent == 319
        assert fitSession.average_heart_rate is None
        assert fitSession.workout_type == WorkoutType.BIKING
