import logging
import os
import random
import shutil
import uuid
from datetime import datetime, timedelta, date

from dateutil.relativedelta import relativedelta
from faker import Faker

from logic import Constants
from logic.model.MonthGoal import MonthGoalDistance, MonthGoalCount
from logic.model.Track import Track, TrackType
from logic.model.User import User, create_user, Language
from logic.model.db import db

LOGGER = logging.getLogger(Constants.APP_NAME)


class DummyDataGenerator:
    NUMBER_OF_MONTHS = 3
    NUMBER_OF_TRACKS_PER_MONTH_BIKING = 7
    NUMBER_OF_TRACKS_PER_MONTH_RUNNING = 2
    AVERAGE_SPEED_IN_KMH_BIKING = 22
    AVERAGE_SPEED_IN_KMH_RUNNING = 10
    TRACK_NAMES = ['Short trip', 'Afterwork I', 'Afterwork II', 'Berlin + Potsdam', 'Megatour']
    GPX_FILE_NAMES = ['gpxTrack_1.gpx', 'gpxTrack_2.gpx']

    def __init__(self, uploadFolder: str):
        self._now = datetime.now().date()
        self._previousMonth = self._now - timedelta(days=30)
        self._previousPreviousMonth = self._previousMonth - timedelta(days=30)
        self._uploadFolder = uploadFolder

    def generate(self) -> None:
        user = self.__generate_demo_user()

        if Track.query.count() == 0:
            self.__generate_demo_tracks_biking(user)
            self.__generate_demo_tracks_running(user)
            self.__generate_demo_month_goals(user)

    @staticmethod
    def __generate_demo_user() -> User:
        user = User.query.filter_by(username='demo').first()

        if user is None:
            LOGGER.debug(f'Creating demo user')
            user = create_user(username='demo', password='demo', isAdmin=False, language=Language.ENGLISH)

        return user

    def __generate_demo_month_goals(self, user) -> None:
        db.session.add(MonthGoalDistance(type=TrackType.BIKING,
                                         year=self._now.year,
                                         month=self._now.month,
                                         distance_minimum=100 * 1000,
                                         distance_perfect=200 * 1000,
                                         user_id=user.id))

        db.session.add(MonthGoalDistance(type=TrackType.BIKING,
                                         year=self._previousMonth.year,
                                         month=self._previousMonth.month,
                                         distance_minimum=200 * 1000,
                                         distance_perfect=400 * 1000,
                                         user_id=user.id))

        db.session.add(MonthGoalDistance(type=TrackType.BIKING,
                                         year=self._previousPreviousMonth.year,
                                         month=self._previousPreviousMonth.month,
                                         distance_minimum=400 * 1000,
                                         distance_perfect=600 * 1000,
                                         user_id=user.id))

        db.session.add(MonthGoalCount(type=TrackType.RUNNING,
                                      year=self._now.year,
                                      month=self._now.month,
                                      count_minimum=1,
                                      count_perfect=4,
                                      user_id=user.id))

        db.session.commit()

    def __generate_demo_tracks_biking(self, user) -> None:
        LOGGER.debug('Generate dummy tracks BIKING...')

        fake = Faker()

        lastDayCurrentMonth = datetime.now().date() + relativedelta(day=31)

        for monthIndex in range(self.NUMBER_OF_MONTHS):
            firstDay = date(year=lastDayCurrentMonth.year, month=lastDayCurrentMonth.month, day=1)

            indexesWithGpx = random.choices(range(self.NUMBER_OF_TRACKS_PER_MONTH_BIKING), k=2)

            for index in range(self.NUMBER_OF_TRACKS_PER_MONTH_BIKING):
                fakeTime = fake.date_time_between_dates(firstDay, lastDayCurrentMonth)
                distance = round(random.uniform(15.00, 50.00), 2)
                duration = distance / self.AVERAGE_SPEED_IN_KMH_BIKING * 60 * 60
                heartRate = random.randint(85, 160)
                elevationSum = random.randint(17, 650)

                track = Track(type=TrackType.BIKING,
                              name=random.choice(self.TRACK_NAMES),
                              startTime=fakeTime,
                              duration=duration,
                              distance=distance * 1000,
                              averageHeartRate=heartRate,
                              elevationSum=elevationSum,
                              user_id=user.id,
                              custom_fields={})

                if index in indexesWithGpx:
                    self.__append_gpx(track)

                db.session.add(track)

            lastDayCurrentMonth = lastDayCurrentMonth - relativedelta(months=1)

        db.session.commit()

    def __append_gpx(self, track: Track) -> None:
        filename = f'{uuid.uuid4().hex}.gpx'
        destinationPath = os.path.join(self._uploadFolder, filename)

        currentDirectory = os.path.abspath(os.path.dirname(__file__))
        dummyDataDirectory = os.path.join(os.path.dirname(currentDirectory), 'dummyData')
        sourcePath = os.path.join(dummyDataDirectory, random.choice(self.GPX_FILE_NAMES))

        shutil.copy2(sourcePath, destinationPath)
        track.gpxFileName = filename

    def __generate_demo_tracks_running(self, user) -> None:
        LOGGER.debug('Generate dummy tracks RUNNING...')

        fake = Faker()

        lastDayCurrentMonth = datetime.now().date() + relativedelta(day=31)

        for monthIndex in range(self.NUMBER_OF_MONTHS):
            firstDay = date(year=lastDayCurrentMonth.year, month=lastDayCurrentMonth.month, day=1)

            for index in range(self.NUMBER_OF_TRACKS_PER_MONTH_RUNNING):
                fakeTime = fake.date_time_between_dates(firstDay, lastDayCurrentMonth)
                distance = round(random.uniform(2.00, 5.00), 2)
                duration = distance / self.AVERAGE_SPEED_IN_KMH_RUNNING * 60 * 60
                heartRate = random.randint(90, 180)

                db.session.add(Track(type=TrackType.RUNNING,
                                     name=random.choice(self.TRACK_NAMES),
                                     startTime=fakeTime,
                                     duration=duration,
                                     distance=distance * 1000,
                                     averageHeartRate=heartRate,
                                     elevationSum=None,
                                     user_id=user.id,
                                     custom_fields={}))

            lastDayCurrentMonth = lastDayCurrentMonth - relativedelta(months=1)

        db.session.commit()
