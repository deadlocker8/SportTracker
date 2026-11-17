import time
from datetime import date

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from sporttracker.db import db
from sporttracker.equipment.clothes.ClothesEntity import Clothes
from sporttracker.equipment.clothes.ClothesType import ClothesType
from sporttracker.user.UserEntity import Language, create_user
from sporttracker.workout.fitness.FitnessWorkoutEntity import FitnessWorkout
from sporttracker.workout.WorkoutType import WorkoutType
from tests.SeleniumTestBaseClass import SeleniumTestBaseClass
from tests.TestConstants import TEST_PASSWORD, TEST_USERNAME


@pytest.fixture(autouse=True)
def prepare_test_data(app):
    with app.app_context():
        user = create_user(TEST_USERNAME, TEST_PASSWORD, False, Language.ENGLISH, 2026)
        db.session.add(
            Clothes(
                name='My Clothes',
                workout_type=WorkoutType.FITNESS,
                is_owned=True,
                purchase_date=date(2021, 1, 1),
                clothes_type=ClothesType.TOPS,
                is_active=True,
                user_id=user.id,
            )
        )
        db.session.commit()


class TestFitnessWorkouts(SeleniumTestBaseClass):
    def __open_form(self, selenium, buttonIndex=0, expectedHeadline='New Biking Workout'):
        selenium.get(self.build_url('/workouts'))

        selenium.find_element(By.CLASS_NAME, 'headline').find_element(By.TAG_NAME, 'a').click()
        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'New Workout')
        )

        buttons = selenium.find_elements(By.CSS_SELECTOR, 'section .btn')
        buttons[buttonIndex].click()
        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), expectedHeadline)
        )

    @staticmethod
    def __fill_fitness_form(
        selenium,
        name,
        date,
        startTime,
        hours,
        minutes,
        seconds,
        averageHeartRate,
        workoutType,
        fitnessWorkoutCategories,
    ):
        selenium.find_element(By.ID, 'workout-name').send_keys(name)
        selenium.find_element(By.ID, 'workout-date').send_keys(date)
        selenium.find_element(By.ID, 'workout-time').send_keys(startTime)
        selenium.find_element(By.ID, 'workout-duration-hours').send_keys(hours)
        selenium.find_element(By.ID, 'workout-duration-minutes').send_keys(minutes)
        selenium.find_element(By.ID, 'workout-duration-seconds').send_keys(seconds)
        selenium.find_element(By.ID, 'workout-averageHeartRate').send_keys(averageHeartRate)

        selenium.find_element(By.XPATH, f'//label[@for="{workoutType}"]').click()

        for category in fitnessWorkoutCategories:
            selenium.find_element(By.XPATH, f'//label[@for="{category}"]').click()

    @staticmethod
    def __submit_equipment_modal(selenium):
        selenium.find_element(
            By.XPATH,
            '//div[@id="workout-equipment-modal"]//button[text()="Apply"]',
        ).click()
        WebDriverWait(selenium, 5).until(
            expected_conditions.invisibility_of_element_located((By.ID, 'workout-equipment-modal'))
        )

    def test_add_fitness_workout_valid(self, server, selenium: WebDriver):
        self.login(selenium)
        self.__open_form(selenium, buttonIndex=3, expectedHeadline='New Fitness Workout')
        self.__fill_fitness_form(
            selenium,
            'My Workout',
            '2023-02-01',
            '15:30',
            0,
            1,
            13,
            46,
            'workout-type-2',
            ['workout-category-1', 'workout-category-2'],
        )
        self.click_button_by_id(selenium, 'buttonSaveWorkout')

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Workouts')
        )

        assert len(selenium.find_elements(By.CSS_SELECTOR, 'section .card-body')) == 1

    def test_add_fitness_workout_with_equipment(self, server, selenium: WebDriver, app):
        with app.app_context():
            clothes_id = Clothes.query.filter(Clothes.name == 'My Clothes').first().id

        self.login(selenium)
        self.__open_form(selenium, buttonIndex=3, expectedHeadline='New Fitness Workout')
        self.__fill_fitness_form(
            selenium,
            'My Workout',
            '2023-02-01',
            '15:30',
            0,
            1,
            13,
            46,
            'workout-type-2',
            ['workout-category-1', 'workout-category-2'],
        )

        buttonEditEquipment = selenium.find_element(By.ID, 'buttonWorkoutEquipmentEdit')
        selenium.execute_script('arguments[0].scrollIntoView();', buttonEditEquipment)
        time.sleep(1)
        buttonEditEquipment.click()

        clothes_card_selector = f'.equipment-modal-card[data-equipment-id="{clothes_id}"]'
        WebDriverWait(selenium, 5).until(
            expected_conditions.visibility_of_element_located((By.CSS_SELECTOR, clothes_card_selector))
        )
        assert selenium.find_elements(By.CSS_SELECTOR, '#workout-equipment-modal .equipment-group-placeholder')

        selected_count = selenium.find_element(By.ID, 'workout-equipment-selected-count')
        assert selected_count.text == '0'

        selenium.execute_script(
            'arguments[0].click();',
            selenium.find_element(By.CSS_SELECTOR, clothes_card_selector),
        )
        clothes_select_icon = selenium.find_element(By.CSS_SELECTOR, f'{clothes_card_selector} .equipment-select-icon')
        assert clothes_select_icon.get_attribute('data-selected') == 'true'
        self.__submit_equipment_modal(selenium)

        assert selected_count.text == '1'
        self.click_button_by_id(selenium, 'buttonSaveWorkout')

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Workouts')
        )

        with app.app_context():
            workout = FitnessWorkout.query.filter(FitnessWorkout.name == 'My Workout').first()
            assert 'equipment_ids' not in workout.custom_fields
            assert [item.name for item in workout.equipment] == ['My Clothes']

    def test_add_fitness_workout_all_empty(self, server, selenium: WebDriver):
        self.login(selenium)
        self.__open_form(selenium, buttonIndex=3, expectedHeadline='New Fitness Workout')
        self.__fill_fitness_form(selenium, '', '', '', '', '', '', '', 'workout-type-1', [])
        self.click_button_by_id(selenium, 'buttonSaveWorkout')

        assert selenium.current_url.endswith('/workouts/add/FITNESS')
