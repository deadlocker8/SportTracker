import datetime

import pytest
from flask_login import FlaskLoginClient, login_user

from sporttracker.logic.AchievementCalculator import AchievementCalculator
from sporttracker.logic.model.DistanceSport import DistanceSport
from sporttracker.logic.model.MonthGoal import MonthGoalDistance, MonthGoalCount
from sporttracker.logic.model.SportType import SportType
from sporttracker.logic.model.User import create_user, Language, User
from sporttracker.logic.model.db import db
from tests.TestConstants import TEST_PASSWORD, TEST_USERNAME


@pytest.fixture(autouse=True)
def prepare_test_data(app):
    app.test_client_class = FlaskLoginClient

    with app.app_context():
        create_user(TEST_USERNAME, TEST_PASSWORD, False, Language.ENGLISH)


def create_dummy_sport(
    sportType: SportType, date: datetime.date, distance: int, duration: int = 2000
) -> DistanceSport:
    return DistanceSport(
        type=sportType,
        name='Dummy Sport',
        start_time=datetime.datetime(
            year=date.year, month=date.month, day=date.day, hour=12, minute=0, second=0
        ),
        duration=duration,
        distance=distance * 1000,
        average_heart_rate=130,
        elevation_sum=16,
        user_id=1,
        custom_fields={},
    )


def create_distance_goal(year, month, distanceMinimum=10, sportType=SportType.BIKING):
    return MonthGoalDistance(
        type=sportType,
        year=year,
        month=month,
        distance_minimum=distanceMinimum * 1000,
        distance_perfect=distanceMinimum * 2 * 1000,
        user_id=1,
    )


def create_count_goal(year, month, countMinimum=1):
    return MonthGoalCount(
        type=SportType.BIKING,
        year=year,
        month=month,
        count_minimum=countMinimum,
        count_perfect=countMinimum * 2,
        user_id=1,
    )


class TestAchievementCalculatorGetLongestDistanceByType:
    def test_get_sport_with_longest_distance_by_type_no_sports_should_return_none(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            result = AchievementCalculator.get_sport_with_longest_distance_by_type(SportType.BIKING)
            assert result is None

    def test_get_sport_with_longest_distance_by_type_multiple_sports_should_return_max_distance(
        self, app
    ):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            db.session.add(create_dummy_sport(SportType.BIKING, datetime.date(2023, 1, 1), 30))
            db.session.add(create_dummy_sport(SportType.BIKING, datetime.date(2023, 2, 1), 50))
            db.session.add(create_dummy_sport(SportType.BIKING, datetime.date(2023, 3, 1), 22))
            db.session.commit()

            result = AchievementCalculator.get_sport_with_longest_distance_by_type(SportType.BIKING)
            assert result is not None
            assert 2 == result.id
            assert 50000 == result.distance


class TestAchievementCalculatorGetLongestDurationByType:
    def test_get_sport_with_longest_duration_by_type_no_sports_should_return_none(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            result = AchievementCalculator.get_sport_with_longest_duration_by_type(
                SportType.FITNESS
            )
            assert result is None

    def test_get_sport_with_longest_duration_by_type_multiple_sports_should_return_max_duration(
        self, app
    ):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            db.session.add(
                create_dummy_sport(SportType.FITNESS, datetime.date(2023, 1, 1), 30, duration=2000)
            )
            db.session.add(
                create_dummy_sport(SportType.FITNESS, datetime.date(2023, 2, 1), 50, duration=4000)
            )
            db.session.add(
                create_dummy_sport(SportType.FITNESS, datetime.date(2023, 3, 1), 22, duration=3000)
            )
            db.session.commit()

            result = AchievementCalculator.get_sport_with_longest_duration_by_type(
                SportType.FITNESS
            )
            assert result is not None
            assert 2 == result.id
            assert 4000 == result.duration


class TestAchievementCalculatorGetTotalDistanceByType:
    def test_get_total_distance_by_type_no_sports_should_return_0(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            result = AchievementCalculator.get_total_distance_by_type(SportType.BIKING)
            assert 0 == result

    def test_get_total_distance_by_type_multiple_sports_should_return_max_distance(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            db.session.add(
                create_dummy_sport(SportType.FITNESS, datetime.date(2023, 1, 1), 30, duration=2000)
            )
            db.session.add(
                create_dummy_sport(SportType.FITNESS, datetime.date(2023, 2, 1), 50, duration=4000)
            )
            db.session.add(
                create_dummy_sport(SportType.FITNESS, datetime.date(2023, 3, 1), 22, duration=3000)
            )
            db.session.commit()

            result = AchievementCalculator.get_total_duration_by_type(SportType.FITNESS)
            assert 9000 == result


class TestAchievementCalculatorGetTotalDurationByType:
    def test_get_total_duration_by_type_no_sports_should_return_0(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            result = AchievementCalculator.get_total_distance_by_type(SportType.FITNESS)
            assert 0 == result

    def test_get_total_duration_by_type_multiple_sports_should_return_max_duration(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            db.session.add(create_dummy_sport(SportType.BIKING, datetime.date(2023, 1, 1), 30))
            db.session.add(create_dummy_sport(SportType.BIKING, datetime.date(2023, 2, 1), 50))
            db.session.add(create_dummy_sport(SportType.BIKING, datetime.date(2023, 3, 1), 22))
            db.session.commit()

            result = AchievementCalculator.get_total_distance_by_type(SportType.BIKING)
            assert 102 == result


class TestAchievementCalculatorGetBestDistanceMonthByType:
    def test_get_best_distance_month_by_type_no_sports_should_return_0(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            result = AchievementCalculator.get_best_distance_month_by_type(SportType.BIKING)
            assert ('No month', 0) == result

    def test_get_best_distance_month_by_type_single_months(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            db.session.add(create_dummy_sport(SportType.BIKING, datetime.date(2023, 1, 1), 30))
            db.session.commit()

            result = AchievementCalculator.get_best_distance_month_by_type(SportType.BIKING)
            assert ('January 2023', 30) == result

    def test_get_best_distance_month_by_type_multiple_months(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            db.session.add(create_dummy_sport(SportType.BIKING, datetime.date(2023, 1, 1), 30))
            db.session.add(create_dummy_sport(SportType.BIKING, datetime.date(2023, 2, 1), 22))
            db.session.add(create_dummy_sport(SportType.BIKING, datetime.date(2023, 2, 5), 30))
            db.session.add(create_dummy_sport(SportType.BIKING, datetime.date(2023, 3, 1), 22))
            db.session.commit()

            result = AchievementCalculator.get_best_distance_month_by_type(SportType.BIKING)
            assert ('February 2023', 52) == result


class TestAchievementCalculatorGetBestDurationMonthByType:
    def test_get_best_duration_month_by_type_no_sports_should_return_0(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            result = AchievementCalculator.get_best_duration_month_by_type(SportType.FITNESS)
            assert ('No month', 0) == result

    def test_get_best_duration_month_by_type_single_months(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            db.session.add(
                create_dummy_sport(SportType.FITNESS, datetime.date(2023, 1, 1), 30, duration=3000)
            )
            db.session.commit()

            result = AchievementCalculator.get_best_duration_month_by_type(SportType.FITNESS)
            assert ('January 2023', 3000) == result

    def test_get_best_duration_month_by_type_multiple_months(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            db.session.add(
                create_dummy_sport(SportType.FITNESS, datetime.date(2023, 1, 1), 30, duration=2000)
            )
            db.session.add(
                create_dummy_sport(SportType.FITNESS, datetime.date(2023, 2, 1), 22, duration=4000)
            )
            db.session.add(
                create_dummy_sport(SportType.FITNESS, datetime.date(2023, 2, 5), 30, duration=3000)
            )
            db.session.add(
                create_dummy_sport(SportType.FITNESS, datetime.date(2023, 3, 1), 22, duration=3500)
            )
            db.session.commit()

            result = AchievementCalculator.get_best_duration_month_by_type(SportType.FITNESS)
            assert ('February 2023', 7000) == result


class TestAchievementCalculatorGetStreaksByType:
    def test_get_streaks_by_type_no_tacks_and_goals_should_return_no_month(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            result = AchievementCalculator.get_streaks_by_type(
                SportType.BIKING, datetime.datetime.now().date()
            )
            assert (0, 0) == result

    def test_get_streaks_by_type_single_month_should_return_month(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            db.session.add(create_distance_goal(2023, 1))

            db.session.add(create_dummy_sport(SportType.BIKING, datetime.date(2023, 1, 1), 30))
            db.session.commit()

            result = AchievementCalculator.get_streaks_by_type(
                SportType.BIKING, datetime.datetime.now().date()
            )
            assert (1, 1) == result

    def test_get_streaks_by_type_multiple_months_should_return_streak_of_two(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            db.session.add(create_distance_goal(2023, 1))
            db.session.add(create_distance_goal(2023, 2))

            db.session.add(create_dummy_sport(SportType.BIKING, datetime.date(2023, 1, 1), 30))
            db.session.add(create_dummy_sport(SportType.BIKING, datetime.date(2023, 2, 1), 30))
            db.session.commit()

            result = AchievementCalculator.get_streaks_by_type(
                SportType.BIKING, datetime.datetime.now().date()
            )
            assert (2, 2) == result

    def test_get_streaks_by_type_multiple_months_streak_broken_between(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            db.session.add(create_distance_goal(2023, 1))
            db.session.add(create_distance_goal(2023, 2))
            db.session.add(create_distance_goal(2023, 3))
            db.session.add(create_distance_goal(2023, 4))

            db.session.add(create_dummy_sport(SportType.BIKING, datetime.date(2023, 1, 1), 30))
            db.session.add(create_dummy_sport(SportType.BIKING, datetime.date(2023, 2, 1), 30))
            db.session.add(create_dummy_sport(SportType.BIKING, datetime.date(2023, 3, 1), 10))
            db.session.add(create_dummy_sport(SportType.BIKING, datetime.date(2023, 4, 1), 30))
            db.session.commit()

            result = AchievementCalculator.get_streaks_by_type(
                SportType.BIKING, datetime.datetime.now().date()
            )
            assert (2, 1) == result

    def test_get_streaks_by_type_multiple_months_with_year_overrun(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            db.session.add(create_distance_goal(2023, 11))
            db.session.add(create_distance_goal(2023, 12))
            db.session.add(create_distance_goal(2024, 1))
            db.session.add(create_distance_goal(2024, 2))

            db.session.add(create_dummy_sport(SportType.BIKING, datetime.date(2023, 11, 1), 30))
            db.session.add(create_dummy_sport(SportType.BIKING, datetime.date(2023, 12, 1), 30))
            db.session.add(create_dummy_sport(SportType.BIKING, datetime.date(2024, 1, 1), 30))
            db.session.add(create_dummy_sport(SportType.BIKING, datetime.date(2024, 2, 1), 30))
            db.session.commit()

            result = AchievementCalculator.get_streaks_by_type(
                SportType.BIKING, datetime.datetime.now().date()
            )
            assert (4, 4) == result

    def test_get_streaks_by_type_multiple_distance_goals_per_month_all_completed(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            db.session.add(create_distance_goal(2023, 1))
            db.session.add(create_distance_goal(2023, 1, distanceMinimum=50))

            db.session.add(create_dummy_sport(SportType.BIKING, datetime.date(2023, 1, 1), 30))
            db.session.add(create_dummy_sport(SportType.BIKING, datetime.date(2023, 1, 1), 80))
            db.session.commit()

            result = AchievementCalculator.get_streaks_by_type(
                SportType.BIKING, datetime.datetime.now().date()
            )
            assert (1, 1) == result

    def test_get_streaks_by_type_multiple_distance_and_count_goals_per_month_all_completed(
        self, app
    ):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            db.session.add(create_distance_goal(2023, 1))
            db.session.add(create_count_goal(2023, 1))

            db.session.add(create_dummy_sport(SportType.BIKING, datetime.date(2023, 1, 1), 30))
            db.session.add(create_dummy_sport(SportType.BIKING, datetime.date(2023, 1, 1), 80))
            db.session.commit()

            result = AchievementCalculator.get_streaks_by_type(
                SportType.BIKING, datetime.datetime.now().date()
            )
            assert (1, 1) == result

    def test_get_streaks_by_type_current_month_already_completed_should_increase_streak(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            db.session.add(create_distance_goal(2023, 1))
            db.session.add(create_distance_goal(2023, 2))
            db.session.add(create_distance_goal(2023, 3))

            db.session.add(create_dummy_sport(SportType.BIKING, datetime.date(2023, 1, 1), 30))
            db.session.add(create_dummy_sport(SportType.BIKING, datetime.date(2023, 2, 1), 30))
            db.session.add(create_dummy_sport(SportType.BIKING, datetime.date(2023, 3, 1), 30))
            db.session.commit()

            result = AchievementCalculator.get_streaks_by_type(
                SportType.BIKING, datetime.date(2023, 3, 1)
            )
            assert (3, 3) == result

    def test_get_streaks_by_type_current_month_not_yet_completed_should_not_break_streak(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            db.session.add(create_distance_goal(2023, 1))
            db.session.add(create_distance_goal(2023, 2))
            db.session.add(create_distance_goal(2023, 3))

            db.session.add(create_dummy_sport(SportType.BIKING, datetime.date(2023, 1, 1), 30))
            db.session.add(create_dummy_sport(SportType.BIKING, datetime.date(2023, 2, 1), 30))
            db.session.commit()

            result = AchievementCalculator.get_streaks_by_type(
                SportType.BIKING, datetime.date(2023, 3, 1)
            )
            assert (2, 2) == result

    def test_get_streaks_by_type_only_check_goals_of_same_type(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            db.session.add(create_distance_goal(2023, 1))
            db.session.add(
                create_distance_goal(2023, 1, distanceMinimum=50, sportType=SportType.RUNNING)
            )

            db.session.add(create_dummy_sport(SportType.BIKING, datetime.date(2023, 1, 1), 30))
            db.session.commit()

            result = AchievementCalculator.get_streaks_by_type(
                SportType.BIKING, datetime.datetime.now().date()
            )
            assert (1, 1) == result


class TestAchievementCalculatorGetAverageSpeedByType:
    def test_get_average_speed_by_type_no_sports_should_return_0(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            result = AchievementCalculator.get_average_speed_by_type_and_year(
                SportType.BIKING, 2023
            )
            assert 0.0 == result

    def test_get_average_speed(self, app):
        with app.test_request_context():
            user = db.session.get(User, 1)
            login_user(user, remember=False)

            sport_1 = create_dummy_sport(SportType.BIKING, datetime.date(2023, 1, 1), 30)
            sport_2 = create_dummy_sport(SportType.BIKING, datetime.date(2023, 2, 1), 50)
            sport_3 = create_dummy_sport(SportType.BIKING, datetime.date(2023, 3, 1), 22)
            sport_4 = create_dummy_sport(SportType.BIKING, datetime.date(2022, 1, 1), 20)
            db.session.add(sport_1)
            db.session.add(sport_2)
            db.session.add(sport_3)
            db.session.add(sport_4)
            db.session.commit()

            result = AchievementCalculator.get_average_speed_by_type_and_year(
                SportType.BIKING, 2023
            )

            speed_1 = sport_1.distance / sport_1.duration * 3.6
            speed_2 = sport_2.distance / sport_2.duration * 3.6
            speed_3 = sport_3.distance / sport_3.duration * 3.6
            expectedSpeed = (speed_1 + speed_2 + speed_3) / 3

            assert expectedSpeed == pytest.approx(result)

            result = AchievementCalculator.get_average_speed_by_type_and_year(
                SportType.BIKING, 2022
            )
            assert sport_4.distance / sport_4.duration * 3.6 == pytest.approx(result)
