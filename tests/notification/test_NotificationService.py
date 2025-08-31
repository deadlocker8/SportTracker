from datetime import datetime

import pytest
from flask_login import FlaskLoginClient, login_user

from sporttracker.db import db
from sporttracker.longDistanceTour.LongDistanceTourEntity import LongDistanceTour
from sporttracker.maintenance.MaintenanceEntity import Maintenance
from sporttracker.maintenance.MaintenanceEventInstanceEntity import MaintenanceEventInstance
from sporttracker.monthGoal.MonthGoalEntity import MonthGoalDistance, MonthGoalCount, MonthGoalDuration
from sporttracker.notification.NotificationService import NotificationService
from sporttracker.notification.NotificationType import NotificationType
from sporttracker.plannedTour.PlannedTourEntity import PlannedTour
from sporttracker.plannedTour.TravelDirection import TravelDirection
from sporttracker.plannedTour.TravelType import TravelType
from sporttracker.user.UserEntity import create_user, Language, User
from sporttracker.workout.WorkoutType import WorkoutType
from sporttracker.workout.distance.DistanceWorkoutEntity import DistanceWorkout
from sporttracker.workout.fitness.FitnessWorkoutEntity import FitnessWorkout
from sporttracker.workout.fitness.FitnessWorkoutType import FitnessWorkoutType
from tests.TestConstants import TEST_USERNAME, TEST_PASSWORD


@pytest.fixture(autouse=True)
def prepare_test_data(app):
    app.test_client_class = FlaskLoginClient

    with app.app_context():
        create_user(TEST_USERNAME, TEST_PASSWORD, False, Language.ENGLISH)
        create_user('USER_2', TEST_PASSWORD, False, Language.ENGLISH)


class TestNotificationService:
    @staticmethod
    def __get_user_by_id(user_id: int) -> User:
        user = db.session.get(User, user_id)
        if user is None:
            raise ValueError(f'Could not find user with id {user_id}')
        return user

    def test_on_distance_workout_updated_check_maintenance_reminders_limit_not_exceeded(self, app):
        with app.test_request_context():
            user_1 = self.__get_user_by_id(2)
            login_user(user_1, remember=False)

            workout = DistanceWorkout(
                type=WorkoutType.BIKING,
                name='Dummy Workout',
                start_time=datetime(year=2025, month=8, day=15, hour=22, minute=1, second=0),
                duration=3600,
                distance=23 * 1000,
                average_heart_rate=130,
                elevation_sum=16,
                user_id=user_1.id,  # type:ignore[union-attr]
                custom_fields={},
            )
            db.session.add(workout)
            db.session.commit()

            maintenance = Maintenance(
                type=WorkoutType.BIKING,
                description='New front tire',
                user_id=user_1.id,
                is_reminder_active=True,
                reminder_limit=200 * 1000,
                custom_workout_field_id=None,
                custom_workout_field_value=None,
            )
            db.session.add(maintenance)
            db.session.commit()

            maintenanceEventInstance = MaintenanceEventInstance(
                event_date=datetime(year=2025, month=8, day=1, hour=12, minute=15, second=0),
                maintenance_id=maintenance.id,
            )
            db.session.add(maintenanceEventInstance)
            db.session.commit()

            notificationService = NotificationService()
            notificationService.on_distance_workout_updated(user_1.id, workout, None, None)

            notifications = notificationService.get_notifications_paginated(0).items
            assert len(notifications) == 0

    def test_on_distance_workout_updated_check_maintenance_reminders_limit_exceeded(self, app):
        with app.test_request_context():
            user_1 = self.__get_user_by_id(2)
            login_user(user_1, remember=False)

            workout = DistanceWorkout(
                type=WorkoutType.BIKING,
                name='Dummy Workout',
                start_time=datetime(year=2025, month=8, day=15, hour=22, minute=1, second=0),
                duration=3600,
                distance=23 * 1000,
                average_heart_rate=130,
                elevation_sum=16,
                user_id=user_1.id,
                custom_fields={},
            )
            db.session.add(workout)
            db.session.commit()

            maintenance = Maintenance(
                type=WorkoutType.BIKING,
                description='New front tire',
                user_id=user_1.id,
                is_reminder_active=True,
                reminder_limit=10 * 1000,
                custom_workout_field_id=None,
                custom_workout_field_value=None,
            )
            db.session.add(maintenance)
            db.session.commit()

            maintenanceEventInstance = MaintenanceEventInstance(
                event_date=datetime(year=2025, month=8, day=1, hour=12, minute=15, second=0),
                maintenance_id=maintenance.id,
            )
            db.session.add(maintenanceEventInstance)
            db.session.commit()

            notificationService = NotificationService()
            notificationService.on_distance_workout_updated(user_1.id, workout, None, None)

            notifications = notificationService.get_notifications_paginated(0).items
            assert len(notifications) == 1
            assert notifications[0].type == NotificationType.MAINTENANCE_REMINDER
            assert notifications[0].user_id == user_1.id
            assert notifications[0].item_id == maintenance.id
            assert notifications[0].message == 'Maintenance "New front tire" exceeds configured limit'
            assert notifications[0].message_details == 'Limit: 10 km, Exceeded by: 13 km'

    def test_on_distance_workout_updated_check_longest_workout_not_longer(self, app):
        with app.test_request_context():
            user_1 = self.__get_user_by_id(2)
            login_user(user_1, remember=False)

            workout = DistanceWorkout(
                type=WorkoutType.BIKING,
                name='Dummy Workout',
                start_time=datetime(year=2025, month=8, day=15, hour=22, minute=1, second=0),
                duration=3600,
                distance=23 * 1000,
                average_heart_rate=130,
                elevation_sum=16,
                user_id=user_1.id,  # type:ignore[union-attr]
                custom_fields={},
            )
            db.session.add(workout)
            db.session.commit()

            notificationService = NotificationService()
            notificationService.on_distance_workout_updated(user_1.id, workout, workout.distance * 2, None)

            notifications = notificationService.get_notifications_paginated(0).items
            assert len(notifications) == 0

    def test_on_distance_workout_updated_check_longest_workout_is_longer(self, app):
        with app.test_request_context():
            user_1 = self.__get_user_by_id(2)
            login_user(user_1, remember=False)

            workout = DistanceWorkout(
                type=WorkoutType.BIKING,
                name='Dummy Workout',
                start_time=datetime(year=2025, month=8, day=15, hour=22, minute=1, second=0),
                duration=3600,
                distance=23 * 1000,
                average_heart_rate=130,
                elevation_sum=16,
                user_id=user_1.id,  # type:ignore[union-attr]
                custom_fields={},
            )
            db.session.add(workout)
            db.session.commit()

            notificationService = NotificationService()
            notificationService.on_distance_workout_updated(user_1.id, workout, workout.distance - 1000, None)

            notifications = notificationService.get_notifications_paginated(0).items
            assert len(notifications) == 1
            assert notifications[0].type == NotificationType.LONGEST_WORKOUT
            assert notifications[0].user_id == user_1.id
            assert notifications[0].item_id == workout.id
            assert notifications[0].message == 'You completed a new distance record with 23.0 km in one Biking workout'
            assert notifications[0].message_details is None

    def test_on_distance_workout_updated_check_best_month_not_longer(self, app):
        with app.test_request_context():
            user_1 = self.__get_user_by_id(2)
            login_user(user_1, remember=False)

            workout = DistanceWorkout(
                type=WorkoutType.BIKING,
                name='Dummy Workout',
                start_time=datetime(year=2025, month=8, day=15, hour=22, minute=1, second=0),
                duration=3600,
                distance=23 * 1000,
                average_heart_rate=130,
                elevation_sum=16,
                user_id=user_1.id,  # type:ignore[union-attr]
                custom_fields={},
            )
            db.session.add(workout)
            db.session.commit()

            notificationService = NotificationService()
            notificationService.on_distance_workout_updated(user_1.id, workout, None, workout.distance * 2)

            notifications = notificationService.get_notifications_paginated(0).items
            assert len(notifications) == 0

    def test_on_distance_workout_updated_check_best_month_is_longer(self, app):
        with app.test_request_context():
            user_1 = self.__get_user_by_id(2)
            login_user(user_1, remember=False)

            workout = DistanceWorkout(
                type=WorkoutType.BIKING,
                name='Dummy Workout',
                start_time=datetime(year=2025, month=8, day=15, hour=22, minute=1, second=0),
                duration=3600,
                distance=23 * 1000,
                average_heart_rate=130,
                elevation_sum=16,
                user_id=user_1.id,  # type:ignore[union-attr]
                custom_fields={},
            )
            db.session.add(workout)
            db.session.commit()

            notificationService = NotificationService()
            notificationService.on_distance_workout_updated(user_1.id, workout, None, 0)

            notifications = notificationService.get_notifications_paginated(0).items
            assert len(notifications) == 1
            assert notifications[0].type == NotificationType.BEST_MONTH
            assert notifications[0].user_id == user_1.id
            assert notifications[0].item_id is None
            assert notifications[0].message == 'August 2025 is now your best Biking month with 23.0 km'
            assert notifications[0].message_details is None

    def test_on_fitness_workout_updated_check_longest_workout_not_longer(self, app):
        with app.test_request_context():
            user_1 = self.__get_user_by_id(2)
            login_user(user_1, remember=False)

            workout = FitnessWorkout(
                type=WorkoutType.FITNESS,
                name='Dummy Workout',
                start_time=datetime(year=2025, month=8, day=15, hour=22, minute=1, second=0),
                duration=3600,
                average_heart_rate=130,
                user_id=user_1.id,  # type:ignore[union-attr]
                fitness_workout_type=FitnessWorkoutType.DURATION_BASED,
                custom_fields={},
            )
            db.session.add(workout)
            db.session.commit()

            notificationService = NotificationService()
            notificationService.on_duration_workout_updated(user_1.id, workout, workout.duration * 2, None)

            notifications = notificationService.get_notifications_paginated(0).items
            assert len(notifications) == 0

    def test_on_fitness_workout_updated_check_longest_workout_is_longer(self, app):
        with app.test_request_context():
            user_1 = self.__get_user_by_id(2)
            login_user(user_1, remember=False)

            workout = FitnessWorkout(
                type=WorkoutType.FITNESS,
                name='Dummy Workout',
                start_time=datetime(year=2025, month=8, day=15, hour=22, minute=1, second=0),
                duration=3600,
                average_heart_rate=130,
                user_id=user_1.id,  # type:ignore[union-attr]
                fitness_workout_type=FitnessWorkoutType.DURATION_BASED,
                custom_fields={},
            )
            db.session.add(workout)
            db.session.commit()

            notificationService = NotificationService()
            notificationService.on_duration_workout_updated(user_1.id, workout, workout.duration - 60, None)

            notifications = notificationService.get_notifications_paginated(0).items
            assert len(notifications) == 1
            assert notifications[0].type == NotificationType.LONGEST_WORKOUT
            assert notifications[0].user_id == user_1.id
            assert notifications[0].item_id == workout.id
            assert notifications[0].message == 'You completed a new duration record with 1:00 h in one Fitness Workout'
            assert notifications[0].message_details is None

    def test_on_fitness_workout_updated_check_best_month_not_longer(self, app):
        with app.test_request_context():
            user_1 = self.__get_user_by_id(2)
            login_user(user_1, remember=False)

            workout = FitnessWorkout(
                type=WorkoutType.FITNESS,
                name='Dummy Workout',
                start_time=datetime(year=2025, month=8, day=15, hour=22, minute=1, second=0),
                duration=3600,
                average_heart_rate=130,
                user_id=user_1.id,  # type:ignore[union-attr]
                fitness_workout_type=FitnessWorkoutType.DURATION_BASED,
                custom_fields={},
            )
            db.session.add(workout)
            db.session.commit()

            notificationService = NotificationService()
            notificationService.on_duration_workout_updated(user_1.id, workout, None, workout.duration * 2)

            notifications = notificationService.get_notifications_paginated(0).items
            assert len(notifications) == 0

    def test_on_fitness_workout_updated_check_best_month_is_longer(self, app):
        with app.test_request_context():
            user_1 = self.__get_user_by_id(2)
            login_user(user_1, remember=False)

            workout = FitnessWorkout(
                type=WorkoutType.FITNESS,
                name='Dummy Workout',
                start_time=datetime(year=2025, month=8, day=15, hour=22, minute=1, second=0),
                duration=3600,
                average_heart_rate=130,
                user_id=user_1.id,  # type:ignore[union-attr]
                fitness_workout_type=FitnessWorkoutType.DURATION_BASED,
                custom_fields={},
            )
            db.session.add(workout)
            db.session.commit()

            notificationService = NotificationService()
            notificationService.on_duration_workout_updated(user_1.id, workout, None, 0)

            notifications = notificationService.get_notifications_paginated(0).items
            assert len(notifications) == 1
            assert notifications[0].type == NotificationType.BEST_MONTH
            assert notifications[0].user_id == user_1.id
            assert notifications[0].item_id is None
            assert notifications[0].message == 'August 2025 is now your best Fitness Workout month with 1:00 h'
            assert notifications[0].message_details is None

    def test_on_planned_tour_created_should_add_notification_for_shared_user(self, app):
        with app.test_request_context():
            user_1 = self.__get_user_by_id(2)
            user_2 = self.__get_user_by_id(3)
            login_user(user_2, remember=False)

            plannedTour = PlannedTour(
                name='Awesome planned tour',
                type=WorkoutType.BIKING,
                user_id=user_2.id,
                creation_date=datetime.now(),
                last_edit_date=datetime.now(),
                last_edit_user_id=user_2.id,
                gpx_metadata_id=None,
                shared_users=[user_1],
                arrival_method=TravelType.NONE,
                departure_method=TravelType.NONE,
                direction=TravelDirection.ROUNDTRIP,
                share_code=None,
            )
            db.session.add(plannedTour)
            db.session.commit()

            notificationService = NotificationService()
            notificationService.on_planned_tour_created(plannedTour)

            login_user(user_1, remember=False)
            notifications = notificationService.get_notifications_paginated(0).items
            assert len(notifications) == 1
            assert notifications[0].type == NotificationType.NEW_SHARED_PLANNED_TOUR
            assert notifications[0].user_id == user_1.id
            assert notifications[0].item_id == plannedTour.id
            assert notifications[0].message == 'User_2 has shared the planned tour "Awesome planned tour" with you'
            assert notifications[0].message_details is None

    def test_on_planned_tour_deleted_should_add_notification_for_shared_user(self, app):
        with app.test_request_context():
            user_1 = self.__get_user_by_id(2)
            user_2 = self.__get_user_by_id(3)
            login_user(user_2, remember=False)

            plannedTour = PlannedTour(
                name='Awesome planned tour',
                type=WorkoutType.BIKING,
                user_id=user_2.id,
                creation_date=datetime.now(),
                last_edit_date=datetime.now(),
                last_edit_user_id=user_2.id,
                gpx_metadata_id=None,
                shared_users=[user_1],
                arrival_method=TravelType.NONE,
                departure_method=TravelType.NONE,
                direction=TravelDirection.ROUNDTRIP,
                share_code=None,
            )

            notificationService = NotificationService()
            notificationService.on_planned_tour_deleted(plannedTour)

            login_user(user_1, remember=False)
            notifications = notificationService.get_notifications_paginated(0).items
            assert len(notifications) == 1
            assert notifications[0].type == NotificationType.DELETED_SHARED_PLANNED_TOUR
            assert notifications[0].user_id == user_1.id
            assert notifications[0].item_id == plannedTour.id
            assert notifications[0].message == 'User_2 has deleted the planned tour "Awesome planned tour"'
            assert notifications[0].message_details is None

    def test_on_planned_tour_updated_shared_user_removed_should_add_notification_for_shared_user(self, app):
        with app.test_request_context():
            user_1 = self.__get_user_by_id(2)
            user_2 = self.__get_user_by_id(3)
            login_user(user_2, remember=False)

            plannedTour = PlannedTour(
                name='Awesome planned tour',
                type=WorkoutType.BIKING,
                user_id=user_2.id,
                creation_date=datetime.now(),
                last_edit_date=datetime.now(),
                last_edit_user_id=user_2.id,
                gpx_metadata_id=None,
                shared_users=[],
                arrival_method=TravelType.NONE,
                departure_method=TravelType.NONE,
                direction=TravelDirection.ROUNDTRIP,
                share_code=None,
            )
            db.session.add(plannedTour)
            db.session.commit()

            notificationService = NotificationService()
            notificationService.on_planned_tour_updated(plannedTour, [user_1])

            login_user(user_1, remember=False)
            notifications = notificationService.get_notifications_paginated(0).items
            assert len(notifications) == 1
            assert notifications[0].type == NotificationType.REVOKED_SHARED_PLANNED_TOUR
            assert notifications[0].user_id == user_1.id
            assert notifications[0].item_id is None
            assert (
                notifications[0].message == 'User_2 has revoked your access to the planned tour "Awesome planned tour"'
            )
            assert notifications[0].message_details is None

    def test_on_planned_tour_updated_shared_user_added_should_add_notification_for_shared_user(self, app):
        with app.test_request_context():
            user_1 = self.__get_user_by_id(2)
            user_2 = self.__get_user_by_id(3)
            login_user(user_2, remember=False)

            plannedTour = PlannedTour(
                name='Awesome planned tour',
                type=WorkoutType.BIKING,
                user_id=user_2.id,
                creation_date=datetime.now(),
                last_edit_date=datetime.now(),
                last_edit_user_id=user_2.id,
                gpx_metadata_id=None,
                shared_users=[user_1],
                arrival_method=TravelType.NONE,
                departure_method=TravelType.NONE,
                direction=TravelDirection.ROUNDTRIP,
                share_code=None,
            )
            db.session.add(plannedTour)
            db.session.commit()

            notificationService = NotificationService()
            notificationService.on_planned_tour_updated(plannedTour, [])

            login_user(user_1, remember=False)
            notifications = notificationService.get_notifications_paginated(0).items
            assert len(notifications) == 1
            assert notifications[0].type == NotificationType.NEW_SHARED_PLANNED_TOUR
            assert notifications[0].user_id == user_1.id
            assert notifications[0].item_id == plannedTour.id
            assert notifications[0].message == 'User_2 has shared the planned tour "Awesome planned tour" with you'
            assert notifications[0].message_details is None

    def test_on_planned_tour_updated_should_add_notification_for_shared_user(self, app):
        with app.test_request_context():
            user_1 = self.__get_user_by_id(2)
            user_2 = self.__get_user_by_id(3)
            login_user(user_2, remember=False)

            plannedTour = PlannedTour(
                name='Awesome planned tour',
                type=WorkoutType.BIKING,
                user_id=user_2.id,
                creation_date=datetime.now(),
                last_edit_date=datetime.now(),
                last_edit_user_id=user_2.id,
                gpx_metadata_id=None,
                shared_users=[user_1],
                arrival_method=TravelType.NONE,
                departure_method=TravelType.NONE,
                direction=TravelDirection.ROUNDTRIP,
                share_code=None,
            )
            db.session.add(plannedTour)
            db.session.commit()

            notificationService = NotificationService()
            notificationService.on_planned_tour_updated(plannedTour, [user_1])

            login_user(user_1, remember=False)
            notifications = notificationService.get_notifications_paginated(0).items
            assert len(notifications) == 1
            assert notifications[0].type == NotificationType.EDITED_SHARED_PLANNED_TOUR
            assert notifications[0].user_id == user_1.id
            assert notifications[0].item_id == plannedTour.id
            assert notifications[0].message == 'User_2 has updated the planned tour "Awesome planned tour"'
            assert notifications[0].message_details is None

    def test_on_planned_tour_updated_by_shared_user_should_not_add_notification_for_owner_but_not_for_shared_user(
        self, app
    ):
        with app.test_request_context():
            user_1 = self.__get_user_by_id(2)
            user_2 = self.__get_user_by_id(3)
            login_user(user_1, remember=False)

            plannedTour = PlannedTour(
                name='Awesome planned tour',
                type=WorkoutType.BIKING,
                user_id=user_2.id,
                creation_date=datetime.now(),
                last_edit_date=datetime.now(),
                last_edit_user_id=user_2.id,
                gpx_metadata_id=None,
                shared_users=[user_1],
                arrival_method=TravelType.NONE,
                departure_method=TravelType.NONE,
                direction=TravelDirection.ROUNDTRIP,
                share_code=None,
            )
            db.session.add(plannedTour)
            db.session.commit()

            notificationService = NotificationService()
            notificationService.on_planned_tour_updated(plannedTour, [user_1])

            login_user(user_1, remember=False)
            notifications = notificationService.get_notifications_paginated(0).items
            assert len(notifications) == 0

            login_user(user_2, remember=False)
            notifications = notificationService.get_notifications_paginated(0).items
            assert len(notifications) == 1
            assert notifications[0].type == NotificationType.EDITED_SHARED_PLANNED_TOUR
            assert notifications[0].user_id == user_2.id
            assert notifications[0].item_id == plannedTour.id
            assert notifications[0].message == 'Test_user has updated the planned tour "Awesome planned tour"'
            assert notifications[0].message_details is None

    ######################

    def test_on_long_distance_tour_created_should_add_notification_for_shared_user(self, app):
        with app.test_request_context():
            user_1 = self.__get_user_by_id(2)
            user_2 = self.__get_user_by_id(3)
            login_user(user_2, remember=False)

            longDistanceTour = LongDistanceTour(
                name='Awesome long-distance tour',
                type=WorkoutType.BIKING,
                user_id=user_2.id,
                creation_date=datetime.now(),
                last_edit_date=datetime.now(),
                last_edit_user_id=user_2.id,
                shared_users=[user_1],
                linked_planned_tours=[],
            )
            db.session.add(longDistanceTour)
            db.session.commit()

            notificationService = NotificationService()
            notificationService.on_long_distance_tour_created(longDistanceTour)

            login_user(user_1, remember=False)
            notifications = notificationService.get_notifications_paginated(0).items
            assert len(notifications) == 1
            assert notifications[0].type == NotificationType.NEW_SHARED_LONG_DISTANCE_TOUR
            assert notifications[0].user_id == user_1.id
            assert notifications[0].item_id == longDistanceTour.id
            assert (
                notifications[0].message
                == 'User_2 has shared the long-distance tour "Awesome long-distance tour" with you'
            )
            assert notifications[0].message_details is None

    def test_on_long_distance_tour_deleted_should_add_notification_for_shared_user(self, app):
        with app.test_request_context():
            user_1 = self.__get_user_by_id(2)
            user_2 = self.__get_user_by_id(3)
            login_user(user_2, remember=False)

            longDistanceTour = LongDistanceTour(
                name='Awesome long-distance tour',
                type=WorkoutType.BIKING,
                user_id=user_2.id,
                creation_date=datetime.now(),
                last_edit_date=datetime.now(),
                last_edit_user_id=user_2.id,
                shared_users=[user_1],
                linked_planned_tours=[],
            )
            db.session.add(longDistanceTour)

            notificationService = NotificationService()
            notificationService.on_long_distance_tour_deleted(longDistanceTour)

            login_user(user_1, remember=False)
            notifications = notificationService.get_notifications_paginated(0).items
            assert len(notifications) == 1
            assert notifications[0].type == NotificationType.DELETED_SHARED_LONG_DISTANCE_TOUR
            assert notifications[0].user_id == user_1.id
            assert notifications[0].item_id is None
            assert notifications[0].message == 'User_2 has deleted the long-distance tour "Awesome long-distance tour"'
            assert notifications[0].message_details is None

    def test_on_long_distance_tour_updated_shared_user_removed_should_add_notification_for_shared_user(self, app):
        with app.test_request_context():
            user_1 = self.__get_user_by_id(2)
            user_2 = self.__get_user_by_id(3)
            login_user(user_2, remember=False)

            longDistanceTour = LongDistanceTour(
                name='Awesome long-distance tour',
                type=WorkoutType.BIKING,
                user_id=user_2.id,
                creation_date=datetime.now(),
                last_edit_date=datetime.now(),
                last_edit_user_id=user_2.id,
                shared_users=[],
                linked_planned_tours=[],
            )
            db.session.add(longDistanceTour)
            db.session.commit()

            notificationService = NotificationService()
            notificationService.on_long_distance_tour_updated(longDistanceTour, [user_1])

            login_user(user_1, remember=False)
            notifications = notificationService.get_notifications_paginated(0).items
            assert len(notifications) == 1
            assert notifications[0].type == NotificationType.REVOKED_SHARED_LONG_DISTANCE_TOUR
            assert notifications[0].user_id == user_1.id
            assert notifications[0].item_id is None
            assert (
                notifications[0].message
                == 'User_2 has revoked your access to the long-distance tour "Awesome long-distance tour"'
            )
            assert notifications[0].message_details is None

    def test_on_long_distance_tour_updated_shared_user_added_should_add_notification_for_shared_user(self, app):
        with app.test_request_context():
            user_1 = self.__get_user_by_id(2)
            user_2 = self.__get_user_by_id(3)
            login_user(user_2, remember=False)

            longDistanceTour = LongDistanceTour(
                name='Awesome long-distance tour',
                type=WorkoutType.BIKING,
                user_id=user_2.id,
                creation_date=datetime.now(),
                last_edit_date=datetime.now(),
                last_edit_user_id=user_2.id,
                shared_users=[user_1],
                linked_planned_tours=[],
            )
            db.session.add(longDistanceTour)
            db.session.commit()

            notificationService = NotificationService()
            notificationService.on_long_distance_tour_updated(longDistanceTour, [])

            login_user(user_1, remember=False)
            notifications = notificationService.get_notifications_paginated(0).items
            assert len(notifications) == 1
            assert notifications[0].type == NotificationType.NEW_SHARED_LONG_DISTANCE_TOUR
            assert notifications[0].user_id == user_1.id
            assert notifications[0].item_id == longDistanceTour.id
            assert (
                notifications[0].message
                == 'User_2 has shared the long-distance tour "Awesome long-distance tour" with you'
            )
            assert notifications[0].message_details is None

    def test_on_long_distance_tour_updated_should_add_notification_for_shared_user(self, app):
        with app.test_request_context():
            user_1 = self.__get_user_by_id(2)
            user_2 = self.__get_user_by_id(3)
            login_user(user_2, remember=False)

            longDistanceTour = LongDistanceTour(
                name='Awesome long-distance tour',
                type=WorkoutType.BIKING,
                user_id=user_2.id,
                creation_date=datetime.now(),
                last_edit_date=datetime.now(),
                last_edit_user_id=user_2.id,
                shared_users=[user_1],
                linked_planned_tours=[],
            )
            db.session.add(longDistanceTour)
            db.session.commit()

            notificationService = NotificationService()
            notificationService.on_long_distance_tour_updated(longDistanceTour, [user_1])

            login_user(user_1, remember=False)
            notifications = notificationService.get_notifications_paginated(0).items
            assert len(notifications) == 1
            assert notifications[0].type == NotificationType.EDITED_SHARED_LONG_DISTANCE_TOUR
            assert notifications[0].user_id == user_1.id
            assert notifications[0].item_id == longDistanceTour.id
            assert notifications[0].message == 'User_2 has updated the long-distance tour "Awesome long-distance tour"'
            assert notifications[0].message_details is None

    def test_on_long_distance_tour_updated_by_shared_user_should_not_add_notification_for_owner_but_not_for_shared_user(
        self, app
    ):
        with app.test_request_context():
            user_1 = self.__get_user_by_id(2)
            user_2 = self.__get_user_by_id(3)
            login_user(user_1, remember=False)

            longDistanceTour = LongDistanceTour(
                name='Awesome long-distance tour',
                type=WorkoutType.BIKING,
                user_id=user_2.id,
                creation_date=datetime.now(),
                last_edit_date=datetime.now(),
                last_edit_user_id=user_2.id,
                shared_users=[user_1],
                linked_planned_tours=[],
            )
            db.session.add(longDistanceTour)
            db.session.commit()

            notificationService = NotificationService()
            notificationService.on_long_distance_tour_updated(longDistanceTour, [user_1])

            login_user(user_1, remember=False)
            notifications = notificationService.get_notifications_paginated(0).items
            assert len(notifications) == 0

            login_user(user_2, remember=False)
            notifications = notificationService.get_notifications_paginated(0).items
            assert len(notifications) == 1
            assert notifications[0].type == NotificationType.EDITED_SHARED_LONG_DISTANCE_TOUR
            assert notifications[0].user_id == user_2.id
            assert notifications[0].item_id == longDistanceTour.id
            assert (
                notifications[0].message == 'Test_user has updated the long-distance tour "Awesome long-distance tour"'
            )
            assert notifications[0].message_details is None

    def test_on_check_month_goals_should_add_notification_for_reached_distance_goal(self, app):
        with app.test_request_context():
            user_1 = self.__get_user_by_id(2)
            login_user(user_1, remember=False)

            monthGoalDistance = MonthGoalDistance(
                type=WorkoutType.BIKING,
                year=2025,
                month=8,
                user_id=user_1.id,
                distance_minimum=100 * 1000,
                distance_perfect=200 * 1000,
            )
            db.session.add(monthGoalDistance)
            db.session.commit()

            workout = DistanceWorkout(
                type=WorkoutType.BIKING,
                name='Dummy Workout',
                start_time=datetime(year=2025, month=8, day=15, hour=22, minute=1, second=0),
                duration=3600,
                distance=250 * 1000,
                average_heart_rate=130,
                elevation_sum=16,
                user_id=user_1.id,  # type:ignore[union-attr]
                custom_fields={},
            )
            db.session.add(workout)
            db.session.commit()

            notificationService = NotificationService()
            notificationService.on_check_month_goals(user_1.id, workout, [])

            notifications = notificationService.get_notifications_paginated(0).items
            assert len(notifications) == 1
            assert notifications[0].type == NotificationType.MONTH_GOAL_DISTANCE
            assert notifications[0].user_id == user_1.id
            assert notifications[0].item_id == monthGoalDistance.id
            assert (
                notifications[0].message == 'You completed your Biking distance month goal "200.0 km" for August 2025'
            )
            assert notifications[0].message_details is None

    def test_on_check_month_goals_should_add_notification_for_reached_count_goal(self, app):
        with app.test_request_context():
            user_1 = self.__get_user_by_id(2)
            login_user(user_1, remember=False)

            monthGoalCount = MonthGoalCount(
                type=WorkoutType.BIKING,
                year=2025,
                month=8,
                user_id=user_1.id,
                count_minimum=1,
                count_perfect=1,
            )
            db.session.add(monthGoalCount)
            db.session.commit()

            workout = DistanceWorkout(
                type=WorkoutType.BIKING,
                name='Dummy Workout',
                start_time=datetime(year=2025, month=8, day=15, hour=22, minute=1, second=0),
                duration=3600,
                distance=36 * 1000,
                average_heart_rate=130,
                elevation_sum=16,
                user_id=user_1.id,  # type:ignore[union-attr]
                custom_fields={},
            )
            db.session.add(workout)
            db.session.commit()

            notificationService = NotificationService()
            notificationService.on_check_month_goals(user_1.id, workout, [])

            notifications = notificationService.get_notifications_paginated(0).items
            assert len(notifications) == 1
            assert notifications[0].type == NotificationType.MONTH_GOAL_COUNT
            assert notifications[0].user_id == user_1.id
            assert notifications[0].item_id == monthGoalCount.id
            assert notifications[0].message == 'You completed your Biking count month goal "1x" for August 2025'
            assert notifications[0].message_details is None

    def test_on_check_month_goals_should_add_notification_for_reached_duration_goal(self, app):
        with app.test_request_context():
            user_1 = self.__get_user_by_id(2)
            login_user(user_1, remember=False)

            monthGoalDuration = MonthGoalDuration(
                type=WorkoutType.FITNESS,
                year=2025,
                month=8,
                user_id=user_1.id,
                duration_minimum=10 * 60,
                duration_perfect=20 * 60,
            )
            db.session.add(monthGoalDuration)
            db.session.commit()

            workout = FitnessWorkout(
                type=WorkoutType.FITNESS,
                name='Dummy Workout',
                start_time=datetime(year=2025, month=8, day=15, hour=22, minute=1, second=0),
                duration=25 * 60,
                average_heart_rate=130,
                user_id=user_1.id,  # type:ignore[union-attr]
                fitness_workout_type=FitnessWorkoutType.DURATION_BASED,
                custom_fields={},
            )
            db.session.add(workout)
            db.session.commit()

            notificationService = NotificationService()
            notificationService.on_check_month_goals(user_1.id, workout, [])

            notifications = notificationService.get_notifications_paginated(0).items
            assert len(notifications) == 1
            assert notifications[0].type == NotificationType.MONTH_GOAL_DURATION
            assert notifications[0].user_id == user_1.id
            assert notifications[0].item_id == monthGoalDuration.id
            assert (
                notifications[0].message
                == 'You completed your Fitness Workout duration month goal "0:20 h" for August 2025'
            )
            assert notifications[0].message_details is None

    def test_on_check_month_goals_should_not_add_notification_if_no_goal_reached(self, app):
        with app.test_request_context():
            user_1 = self.__get_user_by_id(2)
            login_user(user_1, remember=False)

            monthGoalDistance = MonthGoalDistance(
                type=WorkoutType.BIKING,
                year=2025,
                month=8,
                user_id=user_1.id,
                distance_minimum=100 * 1000,
                distance_perfect=200 * 1000,
            )
            db.session.add(monthGoalDistance)
            db.session.commit()

            workout = DistanceWorkout(
                type=WorkoutType.BIKING,
                name='Dummy Workout',
                start_time=datetime(year=2025, month=8, day=15, hour=22, minute=1, second=0),
                duration=3600,
                distance=50 * 1000,
                average_heart_rate=130,
                elevation_sum=16,
                user_id=user_1.id,  # type:ignore[union-attr]
                custom_fields={},
            )
            db.session.add(workout)
            db.session.commit()

            notificationService = NotificationService()
            notificationService.on_check_month_goals(user_1.id, workout, [])

            notifications = notificationService.get_notifications_paginated(0).items
            assert len(notifications) == 0

    def test_on_check_month_goals_should_not_add_notification_if_goal_was_already_reached_before(self, app):
        with app.test_request_context():
            user_1 = self.__get_user_by_id(2)
            login_user(user_1, remember=False)

            monthGoalDistance = MonthGoalDistance(
                type=WorkoutType.BIKING,
                year=2025,
                month=8,
                user_id=user_1.id,
                distance_minimum=100 * 1000,
                distance_perfect=200 * 1000,
            )
            db.session.add(monthGoalDistance)
            db.session.commit()

            workout = DistanceWorkout(
                type=WorkoutType.BIKING,
                name='Dummy Workout',
                start_time=datetime(year=2025, month=8, day=15, hour=22, minute=1, second=0),
                duration=3600,
                distance=250 * 1000,
                average_heart_rate=130,
                elevation_sum=16,
                user_id=user_1.id,  # type:ignore[union-attr]
                custom_fields={},
            )
            db.session.add(workout)
            db.session.commit()

            notificationService = NotificationService()
            notificationService.on_check_month_goals(user_1.id, workout, [monthGoalDistance.get_summary()])

            notifications = notificationService.get_notifications_paginated(0).items
            assert len(notifications) == 0
