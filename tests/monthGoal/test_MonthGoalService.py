from datetime import datetime

import pytest
from flask_login import FlaskLoginClient, login_user

from sporttracker.db import db
from sporttracker.monthGoal.MonthGoalEntity import MonthGoalCount, MonthGoalDistance, MonthGoalDuration
from sporttracker.monthGoal.MonthGoalService import MonthGoalService
from sporttracker.user.UserEntity import Language, User, create_user
from sporttracker.workout.distance.DistanceWorkoutEntity import DistanceWorkout
from sporttracker.workout.WorkoutType import WorkoutType
from tests.TestConstants import TEST_PASSWORD, TEST_USERNAME


@pytest.fixture(autouse=True)
def prepare_test_data(app):
    app.test_client_class = FlaskLoginClient

    with app.app_context():
        create_user(TEST_USERNAME, TEST_PASSWORD, False, Language.ENGLISH, 2026)
        create_user('USER_2', TEST_PASSWORD, False, Language.ENGLISH, 2026)


class TestMonthGoalService:
    @staticmethod
    def __get_user_by_id(user_id: int) -> User:
        user = db.session.get(User, user_id)
        if user is None:
            raise ValueError(f'Could not find user with id {user_id}')
        return user

    def test_get_goal_summaries_for_completed_goals(self, app):
        with app.test_request_context():
            user_1 = self.__get_user_by_id(2)
            login_user(user_1, remember=False)

            goalDistance = MonthGoalDistance(
                type=WorkoutType.BIKING,
                year=2025,
                month=8,
                user_id=user_1.id,  # type:ignore[union-attr]
                distance_minimum=50 * 1000,
                distance_perfect=100 * 1000,
            )
            db.session.add(goalDistance)
            db.session.commit()

            workout = DistanceWorkout(
                type=WorkoutType.BIKING,
                name='Dummy Workout',
                start_time=datetime(year=2025, month=8, day=15, hour=22, minute=1, second=0),
                duration=3600,
                distance=100 * 1000,
                average_heart_rate=130,
                elevation_sum=16,
                user_id=user_1.id,  # type:ignore[union-attr]
                custom_fields={},
            )
            db.session.add(workout)
            db.session.commit()

            goalCount = MonthGoalCount(
                type=WorkoutType.BIKING,
                year=2025,
                month=8,
                user_id=user_1.id,  # type:ignore[union-attr]
                count_minimum=1,
                count_perfect=1,
            )
            db.session.add(goalCount)
            db.session.commit()

            goalDuration = MonthGoalDuration(
                type=WorkoutType.BIKING,
                year=2025,
                month=8,
                user_id=user_1.id,  # type:ignore[union-attr]
                duration_minimum=2000,
                duration_perfect=3000,
            )
            db.session.add(goalDuration)
            db.session.commit()

            goalNotReached = MonthGoalDuration(
                type=WorkoutType.BIKING,
                year=2025,
                month=7,
                user_id=user_1.id,  # type:ignore[union-attr]
                duration_minimum=3000,
                duration_perfect=10000,
            )
            db.session.add(goalNotReached)
            db.session.commit()

            completedGoals = MonthGoalService.get_goal_summaries_for_completed_goals(
                2025,
                8,
                [WorkoutType.BIKING],
                user_1.id,  # type:ignore[union-attr]
            )
            assert len(completedGoals) == 3
            assert completedGoals[0].id == goalDistance.id
            assert completedGoals[1].id == goalCount.id
            assert completedGoals[2].id == goalDuration.id

    def test_get_goal_summaries_new_completed(self, app):
        with app.test_request_context():
            user_1 = self.__get_user_by_id(2)
            login_user(user_1, remember=False)

            goalDistance = MonthGoalDistance(
                type=WorkoutType.BIKING,
                year=2025,
                month=8,
                user_id=user_1.id,  # type:ignore[union-attr]
                distance_minimum=50 * 1000,
                distance_perfect=100 * 1000,
            )
            db.session.add(goalDistance)
            db.session.commit()

            workout = DistanceWorkout(
                type=WorkoutType.BIKING,
                name='Dummy Workout',
                start_time=datetime(year=2025, month=8, day=15, hour=22, minute=1, second=0),
                duration=3600,
                distance=100 * 1000,
                average_heart_rate=130,
                elevation_sum=16,
                user_id=user_1.id,  # type:ignore[union-attr]
                custom_fields={},
            )
            db.session.add(workout)
            db.session.commit()

            goalNotReached = MonthGoalDuration(
                type=WorkoutType.BIKING,
                year=2025,
                month=8,
                user_id=user_1.id,  # type:ignore[union-attr]
                duration_minimum=3000,
                duration_perfect=10000,
            )
            db.session.add(goalNotReached)
            db.session.commit()

            previousCompletedGoals = MonthGoalService.get_goal_summaries_for_completed_goals(
                2025,
                8,
                [WorkoutType.BIKING],
                user_1.id,  # type:ignore[union-attr]
            )

            goalCount = MonthGoalCount(
                type=WorkoutType.BIKING,
                year=2025,
                month=8,
                user_id=user_1.id,  # type:ignore[union-attr]
                count_minimum=1,
                count_perfect=1,
            )
            db.session.add(goalCount)
            db.session.commit()

            completedGoals = MonthGoalService.get_goal_summaries_new_completed(
                2025,
                8,
                [WorkoutType.BIKING],
                user_1.id,  # type:ignore[union-attr]
                previousCompletedGoals,
            )
            assert len(completedGoals) == 1
            assert completedGoals[0].id == goalCount.id

    def test_get_available_years_no_goals(self, app):
        with app.test_request_context():
            user_1 = self.__get_user_by_id(2)
            currentYear = datetime.now().year

            assert MonthGoalService.get_available_years(user_1.id) == [currentYear]  # type:ignore[union-attr]

    def test_get_available_years(self, app):
        with app.test_request_context():
            user_1 = self.__get_user_by_id(2)
            user_2 = self.__get_user_by_id(3)
            currentYear = datetime.now().year

            db.session.add(
                MonthGoalDistance(
                    type=WorkoutType.BIKING,
                    year=currentYear - 2,
                    month=8,
                    user_id=user_1.id,  # type:ignore[union-attr]
                    distance_minimum=50 * 1000,
                    distance_perfect=100 * 1000,
                )
            )
            db.session.add(
                MonthGoalCount(
                    type=WorkoutType.BIKING,
                    year=currentYear,
                    month=8,
                    user_id=user_1.id,  # type:ignore[union-attr]
                    count_minimum=1,
                    count_perfect=1,
                )
            )
            db.session.add(
                MonthGoalDuration(
                    type=WorkoutType.BIKING,
                    year=currentYear - 1,
                    month=9,
                    user_id=user_2.id,  # type:ignore[union-attr]
                    duration_minimum=3000,
                    duration_perfect=10000,
                )
            )
            db.session.commit()

            # years of all goal types are considered and gaps up to the current year are filled
            assert MonthGoalService.get_available_years(user_1.id) == [  # type:ignore[union-attr]
                currentYear - 2,
                currentYear - 1,
                currentYear,
            ]
            # goals of other users are ignored
            assert MonthGoalService.get_available_years(user_2.id) == [  # type:ignore[union-attr]
                currentYear - 1,
                currentYear,
            ]

    def test_get_available_years_with_goals_in_the_future(self, app):
        with app.test_request_context():
            user_1 = self.__get_user_by_id(2)
            currentYear = datetime.now().year

            db.session.add(
                MonthGoalDistance(
                    type=WorkoutType.BIKING,
                    year=currentYear + 2,
                    month=8,
                    user_id=user_1.id,  # type:ignore[union-attr]
                    distance_minimum=50 * 1000,
                    distance_perfect=100 * 1000,
                )
            )
            db.session.commit()

            # a goal far in the future is the only available year
            assert MonthGoalService.get_available_years(user_1.id) == [currentYear + 2]  # type:ignore[union-attr]

            db.session.add(
                MonthGoalCount(
                    type=WorkoutType.BIKING,
                    year=currentYear - 1,
                    month=8,
                    user_id=user_1.id,  # type:ignore[union-attr]
                    count_minimum=1,
                    count_perfect=1,
                )
            )
            db.session.commit()

            # goal years before and after the current year are both kept
            assert MonthGoalService.get_available_years(user_1.id) == [  # type:ignore[union-attr]
                currentYear - 1,
                currentYear,
                currentYear + 1,
                currentYear + 2,
            ]
