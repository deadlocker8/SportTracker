from datetime import date, datetime

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from sporttracker.db import db
from sporttracker.equipment.bike.BikeEntity import Bike
from sporttracker.equipment.clothes.ClothesEntity import Clothes
from sporttracker.equipment.clothes.ClothesType import ClothesType
from sporttracker.equipment.custom.CustomEquipmentEntity import CustomEquipment
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
        bike = Bike(
            workout_type=WorkoutType.BIKING,
            name='Road Bike',
            is_owned=True,
            purchase_date=None,
            is_active=True,
            inactive_date=None,
            user_id=user.id,
        )
        runningShoes = Clothes(
            workout_type=WorkoutType.RUNNING,
            name='Trail Shoes',
            is_owned=True,
            purchase_date=None,
            is_active=True,
            inactive_date=None,
            user_id=user.id,
            clothes_type=ClothesType.SHOES,
        )
        oldMat = CustomEquipment(
            workout_type=WorkoutType.FITNESS,
            name='Old Mat',
            is_owned=True,
            purchase_date=None,
            is_active=False,
            inactive_date=date(2025, 1, 1),
            user_id=user.id,
        )
        db.session.add_all([alice, bob, bike, runningShoes, oldMat])
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
                    equipment=[bike],
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
                    equipment=[],
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
                    equipment=[bike],
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
                    equipment=[runningShoes],
                    custom_fields={},
                ),
                FitnessWorkout(
                    type=WorkoutType.FITNESS,
                    name='Workout Session',
                    start_time=datetime(2025, 3, 10, 10, 0, 0),
                    duration=1800,
                    user_id=user.id,
                    participants=[],
                    equipment=[oldMat],
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
        assert selenium.find_element(By.ID, 'searchFilterAnyParticipant').is_selected()
        assert selenium.find_element(By.ID, 'searchFilterAllEquipment').is_selected()
        assert not selenium.find_element(By.ID, 'buttonSearchEquipmentSelect').is_enabled()
        assert selenium.find_element(By.ID, 'search-equipment-selected-count').text == '3'
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

    def test_filter_by_no_participants(self, server, selenium: WebDriver):
        self.login(selenium)
        selenium.get(self.build_url('/search/search?participantsFilterActive=1'))

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Search Results')
        )

        self.__assert_workout_visible(selenium, 'Long Ride')
        self.__assert_workout_visible(selenium, 'Workout Session')
        self.__assert_workout_not_visible(selenium, 'Morning Ride')
        self.__assert_workout_not_visible(selenium, 'Evening Ride')
        self.__assert_workout_not_visible(selenium, 'Trail Run')

    def test_filter_by_any_participant(self, server, selenium: WebDriver):
        self.login(selenium)
        selenium.get(self.build_url('/search/search?participantsFilterActive=1&anyParticipant=1'))

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Search Results')
        )

        checkboxAnyParticipant = selenium.find_element(By.ID, 'searchFilterAnyParticipant')
        assert checkboxAnyParticipant.is_selected()

        participantCheckboxes = selenium.find_elements(By.CLASS_NAME, 'search-filter-participant-checkbox')
        assert len(participantCheckboxes) > 0
        assert all(not participantCheckbox.is_enabled() for participantCheckbox in participantCheckboxes)

        checkboxAnyParticipant.click()
        assert all(participantCheckbox.is_enabled() for participantCheckbox in participantCheckboxes)

        self.__assert_workout_visible(selenium, 'Morning Ride')
        self.__assert_workout_visible(selenium, 'Long Ride')
        self.__assert_workout_visible(selenium, 'Evening Ride')
        self.__assert_workout_visible(selenium, 'Trail Run')
        self.__assert_workout_visible(selenium, 'Workout Session')

    def test_filter_by_all_participants(self, server, selenium: WebDriver, app):
        with app.app_context():
            alice = Participant.query.filter(Participant.name == 'Alice').first()
            bob = Participant.query.filter(Participant.name == 'Bob').first()
            assert alice is not None
            assert bob is not None
            aliceId = alice.id
            bobId = bob.id

        self.login(selenium)
        selenium.get(
            self.build_url(f'/search/search?participantsFilterActive=1&participants={aliceId}&participants={bobId}')
        )

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Search Results')
        )

        self.__assert_workout_visible(selenium, 'Morning Ride')
        self.__assert_workout_visible(selenium, 'Evening Ride')
        self.__assert_workout_visible(selenium, 'Trail Run')

    def test_filter_by_equipment(self, server, selenium: WebDriver, app):
        with app.app_context():
            bike = Bike.query.filter(Bike.name == 'Road Bike').first()
            assert bike is not None
            bikeId = bike.id

        self.login(selenium)
        selenium.get(self.build_url(f'/search/search?equipmentFilterActive=1&equipment_ids={bikeId}'))

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Search Results')
        )

        self.__assert_workout_visible(selenium, 'Morning Ride')
        self.__assert_workout_visible(selenium, 'Evening Ride')
        self.__assert_workout_not_visible(selenium, 'Long Ride')
        self.__assert_workout_not_visible(selenium, 'Trail Run')
        self.__assert_workout_not_visible(selenium, 'Workout Session')

    def test_filter_by_multiple_equipment_items(self, server, selenium: WebDriver, app):
        with app.app_context():
            bike = Bike.query.filter(Bike.name == 'Road Bike').first()
            runningShoes = Clothes.query.filter(Clothes.name == 'Trail Shoes').first()
            assert bike is not None
            assert runningShoes is not None
            bikeId = bike.id
            runningShoesId = runningShoes.id

        self.login(selenium)
        selenium.get(
            self.build_url(
                f'/search/search?equipmentFilterActive=1&equipment_ids={bikeId}&equipment_ids={runningShoesId}'
            )
        )

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Search Results')
        )

        self.__assert_workout_visible(selenium, 'Morning Ride')
        self.__assert_workout_visible(selenium, 'Evening Ride')
        self.__assert_workout_visible(selenium, 'Trail Run')
        self.__assert_workout_not_visible(selenium, 'Long Ride')
        self.__assert_workout_not_visible(selenium, 'Workout Session')

    def test_filter_by_no_equipment(self, server, selenium: WebDriver):
        self.login(selenium)
        selenium.get(self.build_url('/search/search?equipmentFilterActive=1'))

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Search Results')
        )

        self.__assert_workout_visible(selenium, 'Long Ride')
        self.__assert_workout_not_visible(selenium, 'Morning Ride')
        self.__assert_workout_not_visible(selenium, 'Evening Ride')
        self.__assert_workout_not_visible(selenium, 'Trail Run')
        self.__assert_workout_not_visible(selenium, 'Workout Session')

    def test_all_equipment_checkbox_skips_equipment_filter(self, server, selenium: WebDriver):
        self.login(selenium)
        selenium.get(self.build_url('/search/search?equipmentFilterActive=1&allEquipment=1'))

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Search Results')
        )

        assert selenium.find_element(By.ID, 'searchFilterAllEquipment').is_selected()
        assert not selenium.find_element(By.ID, 'buttonSearchEquipmentSelect').is_enabled()

        self.__assert_workout_visible(selenium, 'Morning Ride')
        self.__assert_workout_visible(selenium, 'Long Ride')
        self.__assert_workout_visible(selenium, 'Evening Ride')
        self.__assert_workout_visible(selenium, 'Trail Run')
        self.__assert_workout_visible(selenium, 'Workout Session')

    def test_filter_by_inactive_equipment(self, server, selenium: WebDriver, app):
        with app.app_context():
            oldMat = CustomEquipment.query.filter(CustomEquipment.name == 'Old Mat').first()
            assert oldMat is not None
            oldMatId = oldMat.id

        self.login(selenium)
        selenium.get(self.build_url(f'/search/search?equipmentFilterActive=1&equipment_ids={oldMatId}'))

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Search Results')
        )

        self.__assert_workout_visible(selenium, 'Workout Session')
        self.__assert_workout_not_visible(selenium, 'Morning Ride')
        self.__assert_workout_not_visible(selenium, 'Long Ride')
        self.__assert_workout_not_visible(selenium, 'Evening Ride')
        self.__assert_workout_not_visible(selenium, 'Trail Run')

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

    def test_quick_filter_preserves_search_filters(self, server, selenium: WebDriver, app):
        with app.app_context():
            bike = Bike.query.filter(Bike.name == 'Road Bike').first()
            assert bike is not None
            bikeId = bike.id

        self.login(selenium)
        selenium.get(self.build_url(f'/search/search?year=2024&equipmentFilterActive=1&equipment_ids={bikeId}'))

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Search Results')
        )

        selenium.find_elements(By.CLASS_NAME, 'quick-filter')[0].click()

        WebDriverWait(selenium, 5).until(
            lambda driver: (
                'year=2024' in driver.current_url
                and 'equipmentFilterActive=1' in driver.current_url
                and f'equipment_ids={bikeId}' in driver.current_url
            )
        )
