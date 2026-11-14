from datetime import datetime

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from sporttracker.db import db
from sporttracker.user.ParticipantEntity import Participant
from sporttracker.user.UserEntity import Language, create_user
from sporttracker.workout.distance.DistanceWorkoutEntity import DistanceWorkout
from sporttracker.workout.fitness.FitnessWorkoutEntity import FitnessWorkout
from sporttracker.workout.fitness.FitnessWorkoutType import FitnessWorkoutType
from sporttracker.workout.WorkoutType import WorkoutType
from tests.SeleniumTestBaseClass import SeleniumTestBaseClass
from tests.TestConstants import TEST_PASSWORD, TEST_USERNAME


@pytest.fixture(autouse=True)
def prepare_test_data(app):
    with app.app_context():
        user = create_user(TEST_USERNAME, TEST_PASSWORD, False, Language.ENGLISH, 2026)

        alice = Participant(name='Alice', user_id=user.id)
        bob = Participant(name='Bob', user_id=user.id)
        db.session.add_all([alice, bob])
        db.session.commit()

        db.session.add_all(
            [
                DistanceWorkout(
                    type=WorkoutType.BIKING,
                    name='Morning Ride',
                    start_time=datetime(2024, 1, 15, 10, 0, 0),
                    duration=3600,
                    distance=25000,
                    user_id=user.id,
                    participants=[alice],
                    custom_fields={},
                ),
                DistanceWorkout(
                    type=WorkoutType.BIKING,
                    name='Long Ride',
                    start_time=datetime(2024, 2, 15, 12, 0, 0),
                    duration=3600,
                    distance=40000,
                    user_id=user.id,
                    participants=[],
                    custom_fields={},
                ),
                DistanceWorkout(
                    type=WorkoutType.BIKING,
                    name='Evening Ride',
                    start_time=datetime(2024, 6, 15, 18, 0, 0),
                    duration=3600,
                    distance=50000,
                    user_id=user.id,
                    participants=[bob],
                    custom_fields={},
                ),
                DistanceWorkout(
                    type=WorkoutType.RUNNING,
                    name='Trail Run',
                    start_time=datetime(2025, 3, 10, 9, 0, 0),
                    duration=3600,
                    distance=10000,
                    user_id=user.id,
                    participants=[alice, bob],
                    custom_fields={},
                ),
                FitnessWorkout(
                    type=WorkoutType.FITNESS,
                    name='Workout Session',
                    start_time=datetime(2025, 3, 10, 10, 0, 0),
                    duration=1800,
                    user_id=user.id,
                    participants=[],
                    custom_fields={},
                    fitness_workout_type=FitnessWorkoutType.DURATION_BASED,
                ),
            ]
        )
        db.session.commit()


class TestSearch(SeleniumTestBaseClass):
    @staticmethod
    def __assert_workout_visible(selenium, workoutName: str) -> None:
        assert (
            len(
                selenium.find_elements(
                    By.XPATH,
                    f'//h4[contains(@class, "card-title") and normalize-space()="{workoutName}"]',
                )
            )
            > 0
        )

    @staticmethod
    def __assert_workout_not_visible(selenium, workoutName: str) -> None:
        assert (
            len(
                selenium.find_elements(
                    By.XPATH,
                    f'//h4[contains(@class, "card-title") and normalize-space()="{workoutName}"]',
                )
            )
            == 0
        )

    def test_search_text_is_prefilled_and_filters_are_visible(self, server, selenium: WebDriver):
        self.login(selenium)
        selenium.get(self.build_url('/search/search?searchText=Ride'))

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Search Results')
        )

        assert selenium.find_element(By.ID, 'searchFilterText').get_attribute('value') == 'Ride'
        assert selenium.find_element(By.ID, 'searchFilterYear').is_displayed()
        assert selenium.find_element(By.ID, 'searchFilterMonth').is_displayed()
        assert selenium.find_element(By.ID, 'searchFilterDistanceMin').is_displayed()
        assert selenium.find_element(By.ID, 'searchFilterDistanceMax').is_displayed()

        self.__assert_workout_visible(selenium, 'Morning Ride')
        self.__assert_workout_visible(selenium, 'Evening Ride')

    def test_filter_by_year_and_month(self, server, selenium: WebDriver):
        self.login(selenium)
        selenium.get(self.build_url('/search/search?year=2024&month=1'))

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Search Results')
        )

        self.__assert_workout_visible(selenium, 'Morning Ride')
        self.__assert_workout_not_visible(selenium, 'Evening Ride')
        self.__assert_workout_not_visible(selenium, 'Trail Run')
        self.__assert_workout_not_visible(selenium, 'Workout Session')

    def test_filter_by_participants(self, server, selenium: WebDriver, app):
        with app.app_context():
            alice = Participant.query.filter(Participant.name == 'Alice').first()
            assert alice is not None
            aliceId = alice.id

        self.login(selenium)
        selenium.get(self.build_url(f'/search/search?participantsFilterActive=1&participants={aliceId}'))

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Search Results')
        )

        self.__assert_workout_visible(selenium, 'Morning Ride')
        self.__assert_workout_visible(selenium, 'Trail Run')
        self.__assert_workout_not_visible(selenium, 'Evening Ride')
        self.__assert_workout_not_visible(selenium, 'Workout Session')

    def test_filter_by_distance_keeps_fitness_workouts(self, server, selenium: WebDriver):
        self.login(selenium)
        selenium.get(self.build_url('/search/search?distanceMin=20&distanceMax=40'))

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Search Results')
        )

        self.__assert_workout_visible(selenium, 'Morning Ride')
        self.__assert_workout_visible(selenium, 'Workout Session')
        self.__assert_workout_not_visible(selenium, 'Evening Ride')
        self.__assert_workout_not_visible(selenium, 'Trail Run')

    def test_filter_by_distance_max(self, server, selenium: WebDriver):
        self.login(selenium)
        selenium.get(self.build_url('/search/search?distanceMin=10&distanceMax=20'))

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Search Results')
        )

        self.__assert_workout_visible(selenium, 'Trail Run')
        self.__assert_workout_visible(selenium, 'Workout Session')
        self.__assert_workout_not_visible(selenium, 'Morning Ride')
        self.__assert_workout_not_visible(selenium, 'Long Ride')
        self.__assert_workout_not_visible(selenium, 'Evening Ride')

    def test_quick_filter_preserves_search_filters(self, server, selenium: WebDriver):
        self.login(selenium)
        selenium.get(self.build_url('/search/search?year=2024'))

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Search Results')
        )

        selenium.find_elements(By.CLASS_NAME, 'quick-filter')[0].click()

        WebDriverWait(selenium, 5).until(lambda driver: 'year=2024' in driver.current_url)
