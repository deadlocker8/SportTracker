from datetime import datetime

import pytest
from flask_login import FlaskLoginClient, login_user

from sporttracker.workout.distance.DistanceWorkoutEntity import DistanceWorkout
from sporttracker.longDistanceTour.LongDistanceTourEntity import LongDistanceTour
from sporttracker.maintenance.MaintenanceEntity import Maintenance
from sporttracker.maintenance.MaintenanceEventInstanceEntity import MaintenanceEventInstance
from sporttracker.logic.model.NotificationType import NotificationType
from sporttracker.plannedTour.PlannedTourEntity import PlannedTour
from sporttracker.plannedTour.TravelDirection import TravelDirection
from sporttracker.plannedTour.TravelType import TravelType
from sporttracker.logic.model.User import create_user, Language, User
from sporttracker.workout.WorkoutType import WorkoutType
from sporttracker.logic.model.db import db
from sporttracker.logic.service.NotificationService import NotificationService
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

    def test_on_distance_workout_updated_limit_not_exceeded(self, app):
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
            notificationService.on_distance_workout_updated(user_1.id, WorkoutType.BIKING)

            notifications = notificationService.get_notifications_paginated(0).items
            assert len(notifications) == 0

    def test_on_distance_workout_updated_limit_exceeded(self, app):
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
            notificationService.on_distance_workout_updated(user_1.id, WorkoutType.BIKING)

            notifications = notificationService.get_notifications_paginated(0).items
            assert len(notifications) == 1
            assert notifications[0].type == NotificationType.MAINTENANCE_REMINDER
            assert notifications[0].user_id == user_1.id
            assert notifications[0].item_id == maintenance.id
            assert notifications[0].message == 'Maintenance "New front tire" exceeds configured limit'
            assert notifications[0].message_details == 'Limit: 10 km, Exceeded by: 13 km'

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
