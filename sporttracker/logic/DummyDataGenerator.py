import logging
import os
import random
import shutil
import uuid
from datetime import datetime, timedelta, date

from dateutil.relativedelta import relativedelta
from faker import Faker

from sporttracker.logic import Constants
from sporttracker.logic.model.CustomTrackField import CustomTrackField, CustomTrackFieldType
from sporttracker.logic.model.MaintenanceEvent import MaintenanceEvent
from sporttracker.logic.model.MonthGoal import MonthGoalDistance, MonthGoalCount
from sporttracker.logic.model.Participant import Participant
from sporttracker.logic.model.PlannedTour import PlannedTour, TravelType, TravelDirection
from sporttracker.logic.model.Track import Track
from sporttracker.logic.model.TrackType import TrackType
from sporttracker.logic.model.User import User, create_user, Language
from sporttracker.logic.model.db import db

LOGGER = logging.getLogger(Constants.APP_NAME)


class DummyDataGenerator:
    NUMBER_OF_MONTHS = 12
    NUMBER_OF_TRACKS_PER_MONTH_BIKING = 7
    NUMBER_OF_TRACKS_PER_MONTH_RUNNING = 2
    NUMBER_OF_TRACKS_PER_MONTH_HIKING = 1
    AVERAGE_SPEED_IN_KMH_BIKING = 22
    AVERAGE_SPEED_IN_KMH_RUNNING = 10
    AVERAGE_SPEED_IN_KMH_HIKING = 4
    TRACK_NAMES = ['Short trip', 'Afterwork I', 'Afterwork II', 'Berlin + Potsdam', 'Megatour']
    GPX_FILE_NAMES = ['gpxTrack_1.gpx', 'gpxTrack_2.gpx']
    MAINTENANCE_EVENT_NAMES = ['chain oiled', 'new pedals', 'new front tire']

    def __init__(self, uploadFolder: str):
        self._now = datetime.now().date()
        self._previousMonth = self._now - timedelta(days=30)
        self._previousPreviousMonth = self._previousMonth - timedelta(days=30)
        self._uploadFolder = uploadFolder

    def generate(self) -> None:
        user = self.__generate_demo_user('demo', 'demo')
        user2 = self.__generate_demo_user('john', '123')

        if Track.query.count() == 0:
            self.__generate_demo_participants(user)

            self.__generate_demo_custom_field(user)

            self.__generate_demo_tracks(
                user=user,
                trackType=TrackType.BIKING,
                numberOfTracksPerMonth=self.NUMBER_OF_TRACKS_PER_MONTH_BIKING,
                numberOfTracksWithGpx=2,
                numberOfTracksWithParticipants=2,
                numberOfTracksWithSharedLink=1,
                averageSpeed=self.AVERAGE_SPEED_IN_KMH_BIKING,
                distanceMin=15.0,
                distanceMax=50.0,
            )

            self.__generate_demo_tracks(
                user=user,
                trackType=TrackType.RUNNING,
                numberOfTracksPerMonth=self.NUMBER_OF_TRACKS_PER_MONTH_RUNNING,
                numberOfTracksWithGpx=2,
                numberOfTracksWithParticipants=0,
                numberOfTracksWithSharedLink=1,
                averageSpeed=self.AVERAGE_SPEED_IN_KMH_RUNNING,
                distanceMin=2.0,
                distanceMax=6.0,
            )

            self.__generate_demo_tracks(
                user=user,
                trackType=TrackType.HIKING,
                numberOfTracksPerMonth=self.NUMBER_OF_TRACKS_PER_MONTH_HIKING,
                numberOfTracksWithGpx=1,
                numberOfTracksWithParticipants=1,
                numberOfTracksWithSharedLink=1,
                averageSpeed=self.AVERAGE_SPEED_IN_KMH_HIKING,
                distanceMin=6.0,
                distanceMax=18.0,
            )

            self.__generate_demo_month_goals(user)

            self.__generate_demo_maintenance_events(user)

            self.__generate_demo_planned_tours(user, user2)

    @staticmethod
    def __generate_demo_user(name: str, password: str) -> User:
        user = User.query.filter_by(username=name).first()

        if user is None:
            LOGGER.debug('Creating demo user')
            user = create_user(
                username=name, password=password, isAdmin=False, language=Language.ENGLISH
            )

        return user

    def __generate_demo_month_goals(self, user) -> None:
        db.session.add(
            MonthGoalDistance(
                type=TrackType.BIKING,
                year=self._now.year,
                month=self._now.month,
                distance_minimum=100 * 1000,
                distance_perfect=200 * 1000,
                user_id=user.id,
            )
        )

        db.session.add(
            MonthGoalDistance(
                type=TrackType.BIKING,
                year=self._previousMonth.year,
                month=self._previousMonth.month,
                distance_minimum=200 * 1000,
                distance_perfect=400 * 1000,
                user_id=user.id,
            )
        )

        db.session.add(
            MonthGoalDistance(
                type=TrackType.BIKING,
                year=self._previousPreviousMonth.year,
                month=self._previousPreviousMonth.month,
                distance_minimum=400 * 1000,
                distance_perfect=600 * 1000,
                user_id=user.id,
            )
        )

        db.session.add(
            MonthGoalCount(
                type=TrackType.RUNNING,
                year=self._now.year,
                month=self._now.month,
                count_minimum=1,
                count_perfect=4,
                user_id=user.id,
            )
        )

        db.session.commit()

    def __generate_demo_tracks(
        self,
        user: User,
        trackType: TrackType,
        numberOfTracksPerMonth: int,
        numberOfTracksWithGpx: int,
        numberOfTracksWithParticipants: int,
        numberOfTracksWithSharedLink: int,
        averageSpeed: int,
        distanceMin: float,
        distanceMax: float,
    ) -> None:
        LOGGER.debug(f'Generate dummy tracks {trackType.name}...')

        fake = Faker()

        lastDayCurrentMonth = datetime.now().date() + relativedelta(day=31)

        for monthIndex in range(self.NUMBER_OF_MONTHS):
            firstDay = date(year=lastDayCurrentMonth.year, month=lastDayCurrentMonth.month, day=1)

            indexesWithGpx = random.choices(range(numberOfTracksPerMonth), k=numberOfTracksWithGpx)
            indexesWithParticipants = random.choices(
                range(numberOfTracksPerMonth), k=numberOfTracksWithParticipants
            )
            indexesWithSharedLink = random.choices(
                range(numberOfTracksPerMonth), k=numberOfTracksWithSharedLink
            )

            for index in range(numberOfTracksPerMonth):
                fakeTime = fake.date_time_between_dates(firstDay, lastDayCurrentMonth)
                distance = round(random.uniform(distanceMin, distanceMax), 2)
                duration = distance / averageSpeed * 60 * 60
                heartRate = random.randint(85, 160)
                elevationSum = random.randint(17, 650)

                track = Track(
                    type=trackType,
                    name=random.choice(self.TRACK_NAMES),
                    startTime=fakeTime,
                    duration=duration,
                    distance=distance * 1000,
                    averageHeartRate=heartRate,
                    elevationSum=elevationSum,
                    user_id=user.id,
                    custom_fields={},
                    share_code=None,
                )

                if index in indexesWithGpx:
                    self.__append_gpx(track)

                if index in indexesWithParticipants:
                    track.participants = [self.__get_participant()]

                if index in indexesWithSharedLink:
                    track.share_code = uuid.uuid4().hex

                db.session.add(track)

            lastDayCurrentMonth = lastDayCurrentMonth - relativedelta(months=1)

        db.session.commit()

    def __append_gpx(self, item: Track | PlannedTour) -> None:
        filename = f'{uuid.uuid4().hex}.gpx'
        destinationPath = os.path.join(self._uploadFolder, filename)

        currentDirectory = os.path.abspath(os.path.dirname(__file__))
        dummyDataDirectory = os.path.join(os.path.dirname(currentDirectory), 'dummyData')
        sourcePath = os.path.join(dummyDataDirectory, random.choice(self.GPX_FILE_NAMES))

        shutil.copy2(sourcePath, destinationPath)
        item.gpxFileName = filename

    def __generate_demo_maintenance_events(self, user) -> None:
        lastDayCurrentMonth = datetime.now().date() + relativedelta(day=31)

        fake = Faker()

        for monthIndex in range(self.NUMBER_OF_MONTHS):
            firstDay = date(year=lastDayCurrentMonth.year, month=lastDayCurrentMonth.month, day=1)
            fakeTime = fake.date_time_between_dates(firstDay, lastDayCurrentMonth)

            db.session.add(
                MaintenanceEvent(
                    type=TrackType.BIKING,
                    event_date=fakeTime,
                    description=random.choice(self.MAINTENANCE_EVENT_NAMES),
                    user_id=user.id,
                )
            )

            lastDayCurrentMonth = lastDayCurrentMonth - relativedelta(months=1)

        db.session.commit()

    def __generate_demo_participants(self, user) -> None:
        db.session.add(Participant(name='John Doe', user_id=user.id))
        db.session.add(Participant(name='Jane', user_id=user.id))
        db.session.commit()

    def __get_participant(self) -> Participant:
        return Participant.query.first()

    def __generate_demo_custom_field(self, user) -> None:
        db.session.add(
            CustomTrackField(
                type=CustomTrackFieldType.STRING,
                track_type=TrackType.BIKING,
                name='Bike',
                is_required=False,
                user_id=user.id,
            )
        )
        db.session.commit()

    def __generate_demo_planned_tours(self, user, user2) -> None:
        fake = Faker()

        for index in range(2):
            fakeTime = fake.date_time_between_dates(
                datetime.now() - timedelta(days=90), datetime.now()
            )

            shared_users = []
            if index == 1:
                shared_users = [user2]

            share_code = None
            if index == 1:
                share_code = uuid.uuid4().hex

            plannedTour = PlannedTour(
                type=TrackType.BIKING,
                creation_date=fakeTime,
                last_edit_date=fakeTime,
                last_edit_user_id=user.id,
                name=random.choice(self.TRACK_NAMES),
                user_id=user.id,
                shared_users=shared_users,
                arrival_method=TravelType.TRAIN,
                departure_method=TravelType.NONE,
                direction=TravelDirection.SINGLE,
                share_code=share_code,
            )

            self.__append_gpx(plannedTour)
            db.session.add(plannedTour)

        db.session.commit()
