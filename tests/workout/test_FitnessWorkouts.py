import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from sporttracker.user.UserEntity import create_user, Language
from tests.SeleniumTestBaseClass import SeleniumTestBaseClass
from tests.TestConstants import TEST_USERNAME, TEST_PASSWORD


@pytest.fixture(autouse=True)
def prepare_test_data(app):
    with app.app_context():
        create_user(TEST_USERNAME, TEST_PASSWORD, False, Language.ENGLISH)


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

    def test_add_fitness_workout_all_empty(self, server, selenium: WebDriver):
        self.login(selenium)
        self.__open_form(selenium, buttonIndex=3, expectedHeadline='New Fitness Workout')
        self.__fill_fitness_form(selenium, '', '', '', '', '', '', '', 'workout-type-1', [])
        self.click_button_by_id(selenium, 'buttonSaveWorkout')

        assert selenium.current_url.endswith('/workouts/add/FITNESS')
