import datetime

import pytest
from flask_login import FlaskLoginClient, login_user

from sporttracker.achievement.AchievementCalculator import AchievementCalculator
from sporttracker.workout.distance.DistanceWorkoutEntity import DistanceWorkout
from sporttracker.monthGoal.MonthGoalEntity import MonthGoalDistance, MonthGoalCount
from sporttracker.user.UserEntity import create_user, Language, User
from sporttracker.workout.WorkoutType import WorkoutType
from sporttracker.db import db
from tests.TestConstants import TEST_PASSWORD, TEST_USERNAME


@pytest.fixture(autouse=True)
def prepare_test_data(app):
    app.test_client_class = FlaskLoginClient

    with app.app_context():
        create_user(TEST_USERNAME, TEST_PASSWORD, False, Language.ENGLISH)


def create_dummy_workout(
    workoutType: WorkoutType, date: datetime.date, distance: int, duration: int = 2000
) -> DistanceWorkout:
    return DistanceWorkout(
        type=workoutType,
        name='Dummy Workout',
        start_time=datetime.datetime(year=date.year, month=date.month, day=date.day, hour=12, minute=0, second=0),
        duration=duration,
        distance=distance * 1000,
        average_heart_rate=130,
        elevation_sum=16,
        user_id=1,
        custom_fields={},
    )


def create_distance_goal(year, month, distanceMinimum=10, workoutType=WorkoutType.BIKING):
    return MonthGoalDistance(
        type=workoutType,
        year=year,
        month=month,
        distance_minimum=distanceMinimum * 1000,
        distance_perfect=distanceMinimum * 2 * 1000,
        user_id=1,
    )


def create_count_goal(year, month, countMinimum=1):
    return MonthGoalCount(
        type=WorkoutType.BIKING,
        year=year,
        month=month,
        count_minimum=countMinimum,
        count_perfect=countMinimum * 2,
        user_id=1,
    )


class TestAchievementCalculatorGetLongestDistanceByType:
    def test_get_workouts_with_longest_distances_by_type_no_workouts_should_return_none(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            result = AchievementCalculator.get_workouts_with_longest_distances_by_type(WorkoutType.BIKING)
            assert len(result) == 0

    def test_get_workouts_with_longest_distances_by_type_multiple_workouts_should_return_max_distance(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            db.session.add(create_dummy_workout(WorkoutType.BIKING, datetime.date(2023, 1, 1), 30))
            db.session.add(create_dummy_workout(WorkoutType.BIKING, datetime.date(2023, 2, 1), 50))
            db.session.add(create_dummy_workout(WorkoutType.BIKING, datetime.date(2023, 3, 1), 22))
            db.session.commit()

            result = AchievementCalculator.get_workouts_with_longest_distances_by_type(WorkoutType.BIKING)
            assert len(result) == 3
            assert result[0].get_date_formatted() == '01.02.2023'
            assert result[0].get_value_formatted() == '50.0 km'

            assert result[1].get_date_formatted() == '01.01.2023'
            assert result[1].get_value_formatted() == '30.0 km'

            assert result[2].get_date_formatted() == '01.03.2023'
            assert result[2].get_value_formatted() == '22.0 km'


class TestAchievementCalculatorGetLongestDurationByType:
    def test_get_workouts_with_longest_durations_by_type_no_workouts_should_return_none(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            result = AchievementCalculator.get_workouts_with_longest_durations_by_type(WorkoutType.FITNESS)
            assert len(result) == 0

    def test_get_workouts_with_longest_durations_by_type_multiple_workouts_should_return_max_duration(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            db.session.add(create_dummy_workout(WorkoutType.FITNESS, datetime.date(2023, 1, 1), 30, duration=2000))
            db.session.add(create_dummy_workout(WorkoutType.FITNESS, datetime.date(2023, 2, 1), 50, duration=4000))
            db.session.add(create_dummy_workout(WorkoutType.FITNESS, datetime.date(2023, 3, 1), 22, duration=3000))
            db.session.commit()

            result = AchievementCalculator.get_workouts_with_longest_durations_by_type(WorkoutType.FITNESS)
            assert len(result) == 3
            assert result[0].get_date_formatted() == '01.02.2023'
            assert result[0].get_value_formatted() == '1:06 h'

            assert result[1].get_date_formatted() == '01.03.2023'
            assert result[1].get_value_formatted() == '0:50 h'

            assert result[2].get_date_formatted() == '01.01.2023'
            assert result[2].get_value_formatted() == '0:33 h'


class TestAchievementCalculatorGetTotalDistanceByType:
    def test_get_total_distance_by_type_no_workouts_should_return_0(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            result = AchievementCalculator.get_total_distance_by_type(WorkoutType.BIKING)
            assert 0 == result

    def test_get_total_distance_by_type_multiple_workouts_should_return_max_distance(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            db.session.add(create_dummy_workout(WorkoutType.FITNESS, datetime.date(2023, 1, 1), 30, duration=2000))
            db.session.add(create_dummy_workout(WorkoutType.FITNESS, datetime.date(2023, 2, 1), 50, duration=4000))
            db.session.add(create_dummy_workout(WorkoutType.FITNESS, datetime.date(2023, 3, 1), 22, duration=3000))
            db.session.commit()

            result = AchievementCalculator.get_total_duration_by_type(WorkoutType.FITNESS)
            assert 9000 == result


class TestAchievementCalculatorGetTotalDurationByType:
    def test_get_total_duration_by_type_no_workouts_should_return_0(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            result = AchievementCalculator.get_total_distance_by_type(WorkoutType.FITNESS)
            assert 0 == result

    def test_get_total_duration_by_type_multiple_workouts_should_return_max_duration(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            db.session.add(create_dummy_workout(WorkoutType.BIKING, datetime.date(2023, 1, 1), 30))
            db.session.add(create_dummy_workout(WorkoutType.BIKING, datetime.date(2023, 2, 1), 50))
            db.session.add(create_dummy_workout(WorkoutType.BIKING, datetime.date(2023, 3, 1), 22))
            db.session.commit()

            result = AchievementCalculator.get_total_distance_by_type(WorkoutType.BIKING)
            assert 102 == result


class TestAchievementCalculatorGetBestDistanceMonthByType:
    def test_get_best_distance_months_by_type_no_workouts_should_return_0(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            result = AchievementCalculator.get_best_distance_months_by_type(WorkoutType.BIKING)
            assert len(result) == 1
            assert result[0].get_value_formatted() == '0.0 km'
            assert result[0].get_date_formatted() == 'No month'

    def test_get_best_distance_months_by_type_single_months(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            db.session.add(create_dummy_workout(WorkoutType.BIKING, datetime.date(2023, 1, 1), 30))
            db.session.commit()

            result = AchievementCalculator.get_best_distance_months_by_type(WorkoutType.BIKING)
            assert len(result) == 1
            assert result[0].get_value_formatted() == '30.0 km'
            assert result[0].get_date_formatted() == 'January 2023'

    def test_get_best_distance_months_by_type_multiple_months(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            db.session.add(create_dummy_workout(WorkoutType.BIKING, datetime.date(2023, 1, 1), 30))
            db.session.add(create_dummy_workout(WorkoutType.BIKING, datetime.date(2023, 2, 1), 22))
            db.session.add(create_dummy_workout(WorkoutType.BIKING, datetime.date(2023, 2, 5), 30))
            db.session.add(create_dummy_workout(WorkoutType.BIKING, datetime.date(2023, 3, 1), 22))
            db.session.commit()

            result = AchievementCalculator.get_best_distance_months_by_type(WorkoutType.BIKING)
            assert len(result) == 3
            assert result[0].get_value_formatted() == '52.0 km'
            assert result[0].get_date_formatted() == 'February 2023'

            assert result[1].get_value_formatted() == '30.0 km'
            assert result[1].get_date_formatted() == 'January 2023'

            assert result[2].get_value_formatted() == '22.0 km'
            assert result[2].get_date_formatted() == 'March 2023'


class TestAchievementCalculatorGetBestDurationMonthByType:
    def test_get_best_duration_month_by_type_no_workouts_should_return_0(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            result = AchievementCalculator.get_best_duration_month_by_type(WorkoutType.FITNESS)
            assert len(result) == 1
            assert result[0].get_value_formatted() == '0:00 h'
            assert result[0].get_date_formatted() == 'No month'

    def test_get_best_duration_month_by_type_single_months(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            db.session.add(create_dummy_workout(WorkoutType.FITNESS, datetime.date(2023, 1, 1), 30, duration=3000))
            db.session.commit()

            result = AchievementCalculator.get_best_duration_month_by_type(WorkoutType.FITNESS)
            assert len(result) == 1
            assert result[0].get_value_formatted() == '0:50 h'
            assert result[0].get_date_formatted() == 'January 2023'

    def test_get_best_duration_month_by_type_multiple_months(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            db.session.add(create_dummy_workout(WorkoutType.FITNESS, datetime.date(2023, 1, 1), 30, duration=2000))
            db.session.add(create_dummy_workout(WorkoutType.FITNESS, datetime.date(2023, 2, 1), 22, duration=4000))
            db.session.add(create_dummy_workout(WorkoutType.FITNESS, datetime.date(2023, 2, 5), 30, duration=3000))
            db.session.add(create_dummy_workout(WorkoutType.FITNESS, datetime.date(2023, 3, 1), 22, duration=3500))
            db.session.commit()

            result = AchievementCalculator.get_best_duration_month_by_type(WorkoutType.FITNESS)
            assert len(result) == 3
            assert result[0].get_value_formatted() == '1:56 h'
            assert result[0].get_date_formatted() == 'February 2023'

            assert result[1].get_value_formatted() == '0:58 h'
            assert result[1].get_date_formatted() == 'March 2023'

            assert result[2].get_value_formatted() == '0:33 h'
            assert result[2].get_date_formatted() == 'January 2023'


class TestAchievementCalculatorGetStreaksByType:
    def test_get_streaks_by_type_no_tacks_and_goals_should_return_no_month(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            result = AchievementCalculator.get_streaks_by_type(WorkoutType.BIKING, datetime.datetime.now().date())
            assert (0, 0) == result

    def test_get_streaks_by_type_single_month_should_return_month(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            db.session.add(create_distance_goal(2023, 1))

            db.session.add(create_dummy_workout(WorkoutType.BIKING, datetime.date(2023, 1, 1), 30))
            db.session.commit()

            result = AchievementCalculator.get_streaks_by_type(WorkoutType.BIKING, datetime.datetime.now().date())
            assert (1, 1) == result

    def test_get_streaks_by_type_multiple_months_should_return_streak_of_two(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            db.session.add(create_distance_goal(2023, 1))
            db.session.add(create_distance_goal(2023, 2))

            db.session.add(create_dummy_workout(WorkoutType.BIKING, datetime.date(2023, 1, 1), 30))
            db.session.add(create_dummy_workout(WorkoutType.BIKING, datetime.date(2023, 2, 1), 30))
            db.session.commit()

            result = AchievementCalculator.get_streaks_by_type(WorkoutType.BIKING, datetime.datetime.now().date())
            assert (2, 2) == result

    def test_get_streaks_by_type_multiple_months_streak_broken_between(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            db.session.add(create_distance_goal(2023, 1))
            db.session.add(create_distance_goal(2023, 2))
            db.session.add(create_distance_goal(2023, 3))
            db.session.add(create_distance_goal(2023, 4))

            db.session.add(create_dummy_workout(WorkoutType.BIKING, datetime.date(2023, 1, 1), 30))
            db.session.add(create_dummy_workout(WorkoutType.BIKING, datetime.date(2023, 2, 1), 30))
            db.session.add(create_dummy_workout(WorkoutType.BIKING, datetime.date(2023, 3, 1), 10))
            db.session.add(create_dummy_workout(WorkoutType.BIKING, datetime.date(2023, 4, 1), 30))
            db.session.commit()

            result = AchievementCalculator.get_streaks_by_type(WorkoutType.BIKING, datetime.datetime.now().date())
            assert (2, 1) == result

    def test_get_streaks_by_type_multiple_months_with_year_overrun(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            db.session.add(create_distance_goal(2023, 11))
            db.session.add(create_distance_goal(2023, 12))
            db.session.add(create_distance_goal(2024, 1))
            db.session.add(create_distance_goal(2024, 2))

            db.session.add(create_dummy_workout(WorkoutType.BIKING, datetime.date(2023, 11, 1), 30))
            db.session.add(create_dummy_workout(WorkoutType.BIKING, datetime.date(2023, 12, 1), 30))
            db.session.add(create_dummy_workout(WorkoutType.BIKING, datetime.date(2024, 1, 1), 30))
            db.session.add(create_dummy_workout(WorkoutType.BIKING, datetime.date(2024, 2, 1), 30))
            db.session.commit()

            result = AchievementCalculator.get_streaks_by_type(WorkoutType.BIKING, datetime.datetime.now().date())
            assert (4, 4) == result

    def test_get_streaks_by_type_multiple_distance_goals_per_month_all_completed(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            db.session.add(create_distance_goal(2023, 1))
            db.session.add(create_distance_goal(2023, 1, distanceMinimum=50))

            db.session.add(create_dummy_workout(WorkoutType.BIKING, datetime.date(2023, 1, 1), 30))
            db.session.add(create_dummy_workout(WorkoutType.BIKING, datetime.date(2023, 1, 1), 80))
            db.session.commit()

            result = AchievementCalculator.get_streaks_by_type(WorkoutType.BIKING, datetime.datetime.now().date())
            assert (1, 1) == result

    def test_get_streaks_by_type_multiple_distance_and_count_goals_per_month_all_completed(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            db.session.add(create_distance_goal(2023, 1))
            db.session.add(create_count_goal(2023, 1))

            db.session.add(create_dummy_workout(WorkoutType.BIKING, datetime.date(2023, 1, 1), 30))
            db.session.add(create_dummy_workout(WorkoutType.BIKING, datetime.date(2023, 1, 1), 80))
            db.session.commit()

            result = AchievementCalculator.get_streaks_by_type(WorkoutType.BIKING, datetime.datetime.now().date())
            assert (1, 1) == result

    def test_get_streaks_by_type_current_month_already_completed_should_increase_streak(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            db.session.add(create_distance_goal(2023, 1))
            db.session.add(create_distance_goal(2023, 2))
            db.session.add(create_distance_goal(2023, 3))

            db.session.add(create_dummy_workout(WorkoutType.BIKING, datetime.date(2023, 1, 1), 30))
            db.session.add(create_dummy_workout(WorkoutType.BIKING, datetime.date(2023, 2, 1), 30))
            db.session.add(create_dummy_workout(WorkoutType.BIKING, datetime.date(2023, 3, 1), 30))
            db.session.commit()

            result = AchievementCalculator.get_streaks_by_type(WorkoutType.BIKING, datetime.date(2023, 3, 1))
            assert (3, 3) == result

    def test_get_streaks_by_type_current_month_not_yet_completed_should_not_break_streak(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            db.session.add(create_distance_goal(2023, 1))
            db.session.add(create_distance_goal(2023, 2))
            db.session.add(create_distance_goal(2023, 3))

            db.session.add(create_dummy_workout(WorkoutType.BIKING, datetime.date(2023, 1, 1), 30))
            db.session.add(create_dummy_workout(WorkoutType.BIKING, datetime.date(2023, 2, 1), 30))
            db.session.commit()

            result = AchievementCalculator.get_streaks_by_type(WorkoutType.BIKING, datetime.date(2023, 3, 1))
            assert (2, 2) == result

    def test_get_streaks_by_type_only_check_goals_of_same_type(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            db.session.add(create_distance_goal(2023, 1))
            db.session.add(create_distance_goal(2023, 1, distanceMinimum=50, workoutType=WorkoutType.RUNNING))

            db.session.add(create_dummy_workout(WorkoutType.BIKING, datetime.date(2023, 1, 1), 30))
            db.session.commit()

            result = AchievementCalculator.get_streaks_by_type(WorkoutType.BIKING, datetime.datetime.now().date())
            assert (1, 1) == result


class TestAchievementCalculatorGetAverageSpeedByType:
    def test_get_average_speed_by_type_no_workouts_should_return_0(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            result = AchievementCalculator.get_average_speed_by_type_and_year(WorkoutType.BIKING, 2023)
            assert 0.0 == result

    def test_get_average_speed(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            workout_1 = create_dummy_workout(WorkoutType.BIKING, datetime.date(2023, 1, 1), 30)
            workout_2 = create_dummy_workout(WorkoutType.BIKING, datetime.date(2023, 2, 1), 50)
            workout_3 = create_dummy_workout(WorkoutType.BIKING, datetime.date(2023, 3, 1), 22)
            workout_4 = create_dummy_workout(WorkoutType.BIKING, datetime.date(2022, 1, 1), 20)
            db.session.add(workout_1)
            db.session.add(workout_2)
            db.session.add(workout_3)
            db.session.add(workout_4)
            db.session.commit()

            result = AchievementCalculator.get_average_speed_by_type_and_year(WorkoutType.BIKING, 2023)

            speed_1 = workout_1.distance / workout_1.duration * 3.6
            speed_2 = workout_2.distance / workout_2.duration * 3.6
            speed_3 = workout_3.distance / workout_3.duration * 3.6
            expectedSpeed = (speed_1 + speed_2 + speed_3) / 3

            assert expectedSpeed == pytest.approx(result)

            result = AchievementCalculator.get_average_speed_by_type_and_year(WorkoutType.BIKING, 2022)
            assert workout_4.distance / workout_4.duration * 3.6 == pytest.approx(result)
