import time

from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait

from tests.SeleniumTestBaseClass import SeleniumTestBaseClass

from tests.blueprints.test_DistanceWorkouts import prepare_test_data  # noqa


class TestWorkouts(SeleniumTestBaseClass):
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

    def __open_edit_form(self, selenium):
        selenium.get(self.build_url('/distanceWorkouts/edit/1'))

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Edit Biking Workout')
        )

    @staticmethod
    def __fill_form(
        selenium,
        name,
        date,
        startTime,
        distance,
        hours,
        minutes,
        seconds,
        averageHeartRate,
        elevationSum,
        plannedTourName='Not based on a Planned Tour',
    ):
        selenium.find_element(By.ID, 'workout-name').send_keys(name)
        selenium.find_element(By.ID, 'workout-date').send_keys(date)
        selenium.find_element(By.ID, 'workout-time').send_keys(startTime)
        selenium.find_element(By.ID, 'workout-distance').send_keys(distance)
        selenium.find_element(By.ID, 'workout-duration-hours').send_keys(hours)
        selenium.find_element(By.ID, 'workout-duration-minutes').send_keys(minutes)
        selenium.find_element(By.ID, 'workout-duration-seconds').send_keys(seconds)
        selenium.find_element(By.ID, 'workout-averageHeartRate').send_keys(averageHeartRate)
        selenium.find_element(By.ID, 'workout-elevationSum').send_keys(elevationSum)

        buttonSave = selenium.find_element(By.ID, 'buttonSaveWorkout')
        selenium.execute_script('arguments[0].scrollIntoView();', buttonSave)
        time.sleep(1)
        select = Select(selenium.find_element(By.ID, 'workout-plannedTour'))
        select.select_by_visible_text(plannedTourName)

    def test_quick_filter_only_show_activated_workout_types(self, server, selenium: WebDriver):
        self.login(selenium)
        self.__open_form(selenium)
        self.__fill_form(selenium, 'My Biking Workout', '2023-02-01', '15:30', 22.5, 1, 13, 46, 123, 650)
        self.click_button_by_id(selenium, 'buttonSaveWorkout')

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Workouts')
        )

        self.__open_form(selenium, buttonIndex=1, expectedHeadline='New Running Workout')
        self.__fill_form(selenium, 'My Running Workout', '2023-02-01', '16:30', 5.5, 0, 20, 12, 188, 15)
        self.click_button_by_id(selenium, 'buttonSaveWorkout')

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Workouts')
        )

        selenium.find_elements(By.CLASS_NAME, 'quick-filter')[0].click()

        WebDriverWait(selenium, 5).until(
            expected_conditions.invisibility_of_element_located((By.XPATH, '//h4[text()="New Biking Workout"]'))
        )

        assert len(selenium.find_elements(By.CSS_SELECTOR, 'section .card-body')) == 1

    def test_month_select(self, server, selenium: WebDriver):
        self.login(selenium)

        selenium.find_element(By.CSS_SELECTOR, '#month-select').click()
        WebDriverWait(selenium, 5).until(expected_conditions.visibility_of_element_located((By.ID, 'headline-years')))

        yearButton = selenium.find_elements(By.CLASS_NAME, 'btn-select-year')[0]
        year = yearButton.get_attribute('data-year')
        yearButton.click()
        WebDriverWait(selenium, 5).until(expected_conditions.visibility_of_element_located((By.ID, 'headline-months')))

        monthIndex = 4
        selenium.find_elements(By.CLASS_NAME, 'btn-select-month')[monthIndex].click()
        WebDriverWait(selenium, 5).until(
            expected_conditions.invisibility_of_element_located((By.ID, 'headline-months'))
        )

        assert selenium.current_url.endswith(f'/workouts/{year}/{monthIndex + 1}')
