import logging
import os
import random
import uuid
from datetime import datetime, timedelta, date

from dateutil.relativedelta import relativedelta
from faker import Faker

from sporttracker.logic import Constants
from sporttracker.logic.GpxService import GpxService
from sporttracker.logic.model.CustomSportField import CustomSportField, CustomSportFieldType
from sporttracker.logic.model.DistanceSport import DistanceSport
from sporttracker.logic.model.GpxMetadata import GpxMetadata
from sporttracker.logic.model.Maintenance import Maintenance
from sporttracker.logic.model.MaintenanceEventInstance import MaintenanceEventInstance
from sporttracker.logic.model.MonthGoal import MonthGoalDistance, MonthGoalCount, MonthGoalDuration
from sporttracker.logic.model.Participant import Participant
from sporttracker.logic.model.PlannedTour import PlannedTour, TravelType, TravelDirection
from sporttracker.logic.model.Sport import Sport
from sporttracker.logic.model.SportType import SportType
from sporttracker.logic.model.User import User, create_user, Language
from sporttracker.logic.model.WorkoutCategory import (
    update_workout_categories_by_sport_id,
    WorkoutCategoryType,
)
from sporttracker.logic.model.WorkoutSport import WorkoutSport
from sporttracker.logic.model.WorkoutType import WorkoutType
from sporttracker.logic.model.db import db

LOGGER = logging.getLogger(Constants.APP_NAME)


class DummyDataGenerator:
    NUMBER_OF_MONTHS = 12
    NUMBER_OF_TRACKS_PER_MONTH_BIKING = 7
    NUMBER_OF_TRACKS_PER_MONTH_RUNNING = 2
    NUMBER_OF_TRACKS_PER_MONTH_HIKING = 1
    NUMBER_OF_TRACKS_PER_MONTH_WORKOUT = 2
    AVERAGE_SPEED_IN_KMH_BIKING = 22
    AVERAGE_SPEED_IN_KMH_RUNNING = 10
    AVERAGE_SPEED_IN_KMH_HIKING = 4
    TRACK_NAMES = ['Short trip', 'Afterwork I', 'Afterwork II', 'Berlin + Potsdam', 'Megatour']
    WORKOUT_NAMES = ['Core Workout', 'HIIT', 'Leg Day', 'Biceps']
    GPX_FILE_NAMES = ['gpxTrack_1.gpx', 'gpxTrack_2.gpx']
    MAINTENANCE_EVENT_NAMES = ['chain oiled', 'new pedals', 'new front tire']

    def __init__(self, gpxService: GpxService):
        self._now = datetime.now().date()
        self._previousMonth = self._now - timedelta(days=30)
        self._previousPreviousMonth = self._previousMonth - timedelta(days=30)
        self._gpxService = gpxService

    def generate(self) -> None:
        user = self.__generate_demo_user('demo', 'demo')
        user2 = self.__generate_demo_user('john', '123')

        if Sport.query.count() == 0:
            self.__generate_demo_participants(user)

            self.__generate_demo_custom_field(user)

            plannedTour = self.__generate_demo_planned_tours(user, user2)

            self.__generate_demo_tracks(
                user=user,
                sportType=SportType.BIKING,
                numberOfTracksPerMonth=self.NUMBER_OF_TRACKS_PER_MONTH_BIKING,
                numberOfTracksWithGpx=2,
                numberOfTracksWithParticipants=2,
                numberOfTracksWithSharedLink=1,
                numberOfTracksWithLinkedPlannedTour=1,
                plannedTour=plannedTour,
                averageSpeed=self.AVERAGE_SPEED_IN_KMH_BIKING,
                distanceMin=15.0,
                distanceMax=50.0,
            )

            self.__generate_demo_tracks(
                user=user,
                sportType=SportType.RUNNING,
                numberOfTracksPerMonth=self.NUMBER_OF_TRACKS_PER_MONTH_RUNNING,
                numberOfTracksWithGpx=2,
                numberOfTracksWithParticipants=0,
                numberOfTracksWithSharedLink=1,
                numberOfTracksWithLinkedPlannedTour=0,
                plannedTour=plannedTour,
                averageSpeed=self.AVERAGE_SPEED_IN_KMH_RUNNING,
                distanceMin=2.0,
                distanceMax=6.0,
            )

            self.__generate_demo_tracks(
                user=user,
                sportType=SportType.HIKING,
                numberOfTracksPerMonth=self.NUMBER_OF_TRACKS_PER_MONTH_HIKING,
                numberOfTracksWithGpx=1,
                numberOfTracksWithParticipants=1,
                numberOfTracksWithSharedLink=1,
                numberOfTracksWithLinkedPlannedTour=0,
                plannedTour=plannedTour,
                averageSpeed=self.AVERAGE_SPEED_IN_KMH_HIKING,
                distanceMin=6.0,
                distanceMax=18.0,
            )

            self.__generate_demo_duration_based_tracks(
                user=user,
                sportType=SportType.WORKOUT,
                numberOfTracksPerMonth=self.NUMBER_OF_TRACKS_PER_MONTH_WORKOUT,
                numberOfTracksWithParticipants=1,
                durationMin=20 * 60,
                durationMax=90 * 60,
            )

            self.__generate_demo_month_goals(user)

            self.__generate_demo_maintenance_events(user)

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
                type=SportType.BIKING,
                year=self._now.year,
                month=self._now.month,
                distance_minimum=100 * 1000,
                distance_perfect=200 * 1000,
                user_id=user.id,
            )
        )

        db.session.add(
            MonthGoalDistance(
                type=SportType.BIKING,
                year=self._previousMonth.year,
                month=self._previousMonth.month,
                distance_minimum=200 * 1000,
                distance_perfect=400 * 1000,
                user_id=user.id,
            )
        )

        db.session.add(
            MonthGoalDistance(
                type=SportType.BIKING,
                year=self._previousPreviousMonth.year,
                month=self._previousPreviousMonth.month,
                distance_minimum=400 * 1000,
                distance_perfect=600 * 1000,
                user_id=user.id,
            )
        )

        db.session.add(
            MonthGoalCount(
                type=SportType.RUNNING,
                year=self._now.year,
                month=self._now.month,
                count_minimum=1,
                count_perfect=4,
                user_id=user.id,
            )
        )

        db.session.add(
            MonthGoalDuration(
                type=SportType.WORKOUT,
                year=self._now.year,
                month=self._now.month,
                duration_minimum=2 * 60 * 60,
                duration_perfect=6 * 60 * 60,
                user_id=user.id,
            )
        )

        db.session.commit()

    def __generate_demo_tracks(
        self,
        user: User,
        sportType: SportType,
        numberOfTracksPerMonth: int,
        numberOfTracksWithGpx: int,
        numberOfTracksWithParticipants: int,
        numberOfTracksWithSharedLink: int,
        numberOfTracksWithLinkedPlannedTour: int,
        plannedTour: PlannedTour,
        averageSpeed: int,
        distanceMin: float,
        distanceMax: float,
    ) -> None:
        LOGGER.debug(f'Generate dummy tracks {sportType.name}...')

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
            indexesWithLinkedPlannedTour = random.choices(
                range(numberOfTracksPerMonth), k=numberOfTracksWithLinkedPlannedTour
            )

            for index in range(numberOfTracksPerMonth):
                fakeTime = fake.date_time_between_dates(firstDay, lastDayCurrentMonth)
                distance = round(random.uniform(distanceMin, distanceMax), 2)
                duration = distance / averageSpeed * 60 * 60
                heartRate = random.randint(85, 160)
                elevationSum = random.randint(17, 650)

                sport = DistanceSport(
                    type=sportType,
                    name=random.choice(self.TRACK_NAMES),
                    start_time=fakeTime,
                    duration=duration,
                    distance=distance * 1000,
                    average_heart_rate=heartRate,
                    elevation_sum=elevationSum,
                    user_id=user.id,
                    custom_fields={},
                    share_code=None,
                )

                if index in indexesWithGpx:
                    self.__append_gpx(sport)

                if index in indexesWithParticipants:
                    sport.participants = [self.__get_participant()]

                if index in indexesWithSharedLink:
                    sport.share_code = uuid.uuid4().hex

                if index in indexesWithLinkedPlannedTour:
                    sport.planned_tour = plannedTour

                db.session.add(sport)
                db.session.commit()

                if index in indexesWithGpx:
                    self._gpxService.add_visited_tiles_for_sport(sport, 14, user.id)

            lastDayCurrentMonth = lastDayCurrentMonth - relativedelta(months=1)

    def __append_gpx(self, item: DistanceSport | PlannedTour) -> None:
        currentDirectory = os.path.abspath(os.path.dirname(__file__))
        dummyDataDirectory = os.path.join(os.path.dirname(currentDirectory), 'dummyData')
        sourcePath = os.path.join(dummyDataDirectory, random.choice(self.GPX_FILE_NAMES))

        filename = uuid.uuid4().hex
        with open(sourcePath, 'rb') as f:
            self._gpxService.create_zip(filename, f.read())

        gpxMetadata = GpxMetadata(
            gpx_file_name=filename,
            length=random.uniform(20 * 1000.0, 60 * 1000.0),
            elevation_minimum=random.randint(30, 200),
            elevation_maximum=random.randint(220, 400),
            uphill=random.randint(30, 400),
            downhill=random.randint(30, 400),
        )

        db.session.add(gpxMetadata)
        db.session.commit()

        item.gpx_metadata_id = gpxMetadata.id

    def __generate_demo_duration_based_tracks(
        self,
        user: User,
        sportType: SportType,
        numberOfTracksPerMonth: int,
        numberOfTracksWithParticipants: int,
        durationMin: int,
        durationMax: int,
    ) -> None:
        LOGGER.debug(f'Generate dummy duration-based tracks {sportType.name}...')

        fake = Faker()

        lastDayCurrentMonth = datetime.now().date() + relativedelta(day=31)

        for monthIndex in range(self.NUMBER_OF_MONTHS):
            firstDay = date(year=lastDayCurrentMonth.year, month=lastDayCurrentMonth.month, day=1)

            indexesWithParticipants = random.choices(
                range(numberOfTracksPerMonth), k=numberOfTracksWithParticipants
            )

            for index in range(numberOfTracksPerMonth):
                fakeTime = fake.date_time_between_dates(firstDay, lastDayCurrentMonth)
                duration = round(random.uniform(durationMin, durationMax), 2)
                workoutType = random.choice([x for x in WorkoutType])
                workoutCategory = random.choice([x for x in WorkoutCategoryType])

                sport = WorkoutSport(
                    name=random.choice(self.WORKOUT_NAMES),
                    type=sportType,
                    start_time=fakeTime,
                    duration=duration,
                    user_id=user.id,
                    custom_fields={},
                    workout_type=workoutType,  # type: ignore[call-arg]
                )

                if index in indexesWithParticipants:
                    sport.participants = [self.__get_participant()]

                db.session.add(sport)
                db.session.commit()

                update_workout_categories_by_sport_id(sport.id, [workoutCategory])

            lastDayCurrentMonth = lastDayCurrentMonth - relativedelta(months=1)

    def __generate_demo_maintenance_events(self, user) -> None:
        lastDayCurrentMonth = datetime.now().date()

        fake = Faker()

        maintenances = []
        for name in self.MAINTENANCE_EVENT_NAMES:
            maintenance = Maintenance(
                type=SportType.BIKING,
                description=name,
                user_id=user.id,
                is_reminder_active=True,
                reminder_limit=200 * 1000,
            )

            db.session.add(maintenance)
            maintenances.append(maintenance)

        db.session.commit()

        for monthIndex in range(self.NUMBER_OF_MONTHS):
            firstDay = date(year=lastDayCurrentMonth.year, month=lastDayCurrentMonth.month, day=1)
            fakeTime = fake.date_time_between_dates(firstDay, lastDayCurrentMonth)

            db.session.add(
                MaintenanceEventInstance(
                    event_date=fakeTime,
                    maintenance_id=random.choice(maintenances).id,
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
            CustomSportField(
                type=CustomSportFieldType.STRING,
                sport_type=SportType.BIKING,
                name='Bike',
                is_required=False,
                user_id=user.id,
            )
        )
        db.session.commit()

    def __generate_demo_planned_tours(self, user, user2) -> PlannedTour:
        fake = Faker()

        lastPlannedTour = None

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
                type=SportType.BIKING,
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
            lastPlannedTour = plannedTour

        db.session.commit()

        return lastPlannedTour  # type: ignore[return-value]
