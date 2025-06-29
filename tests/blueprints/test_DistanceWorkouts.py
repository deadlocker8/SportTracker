import os
import time
from datetime import datetime

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait

from sporttracker.logic.model.CustomWorkoutField import CustomWorkoutField, CustomWorkoutFieldType
from sporttracker.logic.model.Participant import Participant
from sporttracker.logic.model.PlannedTour import PlannedTour, TravelDirection
from sporttracker.logic.model.TravelType import TravelType
from sporttracker.logic.model.User import create_user, Language, User
from sporttracker.logic.model.WorkoutType import WorkoutType
from sporttracker.logic.model.db import db
from tests.SeleniumTestBaseClass import SeleniumTestBaseClass
from tests.TestConstants import TEST_USERNAME, TEST_PASSWORD, ROOT_DIRECTORY


@pytest.fixture(autouse=True)
def prepare_test_data(app):
    with app.app_context():
        user = create_user(TEST_USERNAME, TEST_PASSWORD, False, Language.ENGLISH)

        plannedTour = PlannedTour(
            id=1,
            type=WorkoutType.BIKING,
            name='Megatour',
            creation_date=datetime.now(),
            last_edit_date=datetime.now(),
            last_edit_user_id=user.id,
            gpx_metadata_id=None,
            user_id=user.id,
            shared_users=[],
            arrival_method=TravelType.TRAIN,
            departure_method=TravelType.NONE,
            direction=TravelDirection.SINGLE,
            share_code=None,
        )
        db.session.add(plannedTour)
        db.session.commit()


class TestDistanceWorkouts(SeleniumTestBaseClass):
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

    def test_add_workout_valid(self, server, selenium: WebDriver):
        self.login(selenium)
        self.__open_form(selenium)
        self.__fill_form(selenium, 'My Workout', '2023-02-01', '15:30', 22.5, 1, 13, 46, 123, 650)
        self.click_button_by_id(selenium, 'buttonSaveWorkout')

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Workouts')
        )

        assert len(selenium.find_elements(By.CSS_SELECTOR, 'section .card-body')) == 1

    def test_add_workout_all_empty(self, server, selenium: WebDriver):
        self.login(selenium)
        self.__open_form(selenium)
        self.__fill_form(selenium, '', '', '', '', '', '', '', '', '')
        self.click_button_by_id(selenium, 'buttonSaveWorkout')

        assert selenium.current_url.endswith('/workouts/add/BIKING')

    def test_add_workout_mandatory_custom_field_not_filled(self, server, selenium: WebDriver, app):
        user = User.query.filter(User.username == TEST_USERNAME).first()

        with app.app_context():
            customWorkoutField = CustomWorkoutField(
                type=CustomWorkoutFieldType.INTEGER,
                workout_type=WorkoutType.BIKING,
                name='my_custom_field',
                is_required=True,
                user_id=user.id,
            )
            db.session.add(customWorkoutField)
            db.session.commit()

        self.login(selenium)
        self.__open_form(selenium)
        self.__fill_form(selenium, 'My Workout', '2023-02-01', '15:30', 22.5, 1, 13, 46, 123, 650)
        self.click_button_by_id(selenium, 'buttonSaveWorkout')

        assert selenium.current_url.endswith('/workouts/add/BIKING')

    def test_add_workout_mandatory_custom_field_filled(self, server, selenium: WebDriver, app):
        user = User.query.filter(User.username == TEST_USERNAME).first()

        with app.app_context():
            customWorkoutField = CustomWorkoutField(
                type=CustomWorkoutFieldType.INTEGER,
                workout_type=WorkoutType.BIKING,
                name='my_custom_field',
                is_required=True,
                user_id=user.id,
            )
            db.session.add(customWorkoutField)
            db.session.commit()

        self.login(selenium)
        self.__open_form(selenium)
        self.__fill_form(selenium, 'My Workout', '2023-02-01', '15:30', 22.5, 1, 13, 46, 123, 650)
        selenium.find_element(By.ID, 'workout-my_custom_field').send_keys('15')
        self.click_button_by_id(selenium, 'buttonSaveWorkout')

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Workouts')
        )

        assert len(selenium.find_elements(By.CSS_SELECTOR, 'section .card-body')) == 1

    def test_add_workout_non_mandatory_custom_field_not_filled(self, server, selenium: WebDriver, app):
        user = User.query.filter(User.username == TEST_USERNAME).first()

        with app.app_context():
            customWorkoutField = CustomWorkoutField(
                type=CustomWorkoutFieldType.INTEGER,
                workout_type=WorkoutType.BIKING,
                name='my_custom_field',
                is_required=False,
                user_id=user.id,
            )
            db.session.add(customWorkoutField)
            db.session.commit()

        self.login(selenium)
        self.__open_form(selenium)
        self.__fill_form(selenium, 'My Workout', '2023-02-01', '15:30', 22.5, 1, 13, 46, 123, 650)
        self.click_button_by_id(selenium, 'buttonSaveWorkout')

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Workouts')
        )

        assert len(selenium.find_elements(By.CSS_SELECTOR, 'section .card-body')) == 1

    def test_add_workout_one_participant_selected(self, server, selenium: WebDriver, app):
        user = User.query.filter(User.username == TEST_USERNAME).first()

        with app.app_context():
            participant = Participant(
                name='John Doe',
                user_id=user.id,
            )
            db.session.add(participant)
            db.session.commit()

        self.login(selenium)
        self.__open_form(selenium)
        self.__fill_form(selenium, 'My Workout', '2023-02-01', '15:30', 22.5, 1, 13, 46, 123, 650)
        selenium.find_element(By.XPATH, '//label[@for="participant-1"]').click()
        self.click_button_by_id(selenium, 'buttonSaveWorkout')

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Workouts')
        )

        cards = selenium.find_elements(By.CSS_SELECTOR, 'section .card-body')
        assert len(cards) == 1
        # check participants icon is displayed
        assert cards[0].find_element(By.XPATH, '//span[text()="group"]')

    def test_add_workout_multiple_participant_selected(self, server, selenium: WebDriver, app):
        user = User.query.filter(User.username == TEST_USERNAME).first()

        with app.app_context():
            participant = Participant(
                name='John Doe',
                user_id=user.id,
            )
            db.session.add(participant)
            participant = Participant(
                name='Jane',
                user_id=user.id,
            )
            db.session.add(participant)
            db.session.commit()

        self.login(selenium)
        self.__open_form(selenium)
        self.__fill_form(selenium, 'My Workout', '2023-02-01', '15:30', 22.5, 1, 13, 46, 123, 650)
        selenium.find_element(By.XPATH, '//label[@for="participant-1"]').click()
        selenium.find_element(By.XPATH, '//label[@for="participant-2"]').click()
        self.click_button_by_id(selenium, 'buttonSaveWorkout')

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Workouts')
        )

        cards = selenium.find_elements(By.CSS_SELECTOR, 'section .card-body')
        assert len(cards) == 1
        # check participants icon is displayed
        assert cards[0].find_element(By.XPATH, '//span[text()="group"]')

    def test_new_workout_share_via_link(self, server, selenium: WebDriver):
        self.login(selenium)
        self.__open_form(selenium)

        self.__fill_form(selenium, 'My Biking Workout', '2023-02-01', '15:30', 22.5, 1, 13, 46, 123, 650)

        self.click_button_by_id(selenium, 'buttonCreateSharedLink')
        WebDriverWait(selenium, 5).until(expected_conditions.visibility_of_element_located((By.ID, 'sharedLink')))
        sharedLink = selenium.find_element(By.ID, 'sharedLink').text
        self.click_button_by_id(selenium, 'buttonSaveWorkout')

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Workouts')
        )

        cards = selenium.find_elements(By.CSS_SELECTOR, 'section .card')
        assert len(cards) == 1
        # check share icon is displayed
        assert cards[0].find_element(By.XPATH, '//span[contains(text(), "share")]')

        # check shared link can be viewed without login
        self.logout(selenium)
        selenium.get(sharedLink)
        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'planned-tour-name'), 'My Biking Workout')
        )

    def test_edit_workout_remove_shared_link(self, server, selenium: WebDriver):
        self.login(selenium)
        self.__open_form(selenium)

        self.__fill_form(selenium, 'My Biking Workout', '2023-02-01', '15:30', 22.5, 1, 13, 46, 123, 650)

        self.click_button_by_id(selenium, 'buttonCreateSharedLink')
        WebDriverWait(selenium, 5).until(expected_conditions.visibility_of_element_located((By.ID, 'sharedLink')))
        sharedLink = selenium.find_element(By.ID, 'sharedLink').text
        self.click_button_by_id(selenium, 'buttonSaveWorkout')

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Workouts')
        )

        self.__open_edit_form(selenium)

        buttonSharedLinkDeleteModal = selenium.find_element(By.ID, 'buttonSharedLinkDeleteModal')
        selenium.execute_script('arguments[0].scrollIntoView();', buttonSharedLinkDeleteModal)
        time.sleep(1)
        buttonSharedLinkDeleteModal.click()
        WebDriverWait(selenium, 5).until(expected_conditions.element_to_be_clickable((By.ID, 'buttonSharedLinkDelete')))
        time.sleep(1)
        selenium.find_element(By.ID, 'buttonSharedLinkDelete').click()
        WebDriverWait(selenium, 5).until(expected_conditions.invisibility_of_element_located((By.ID, 'sharedLink')))
        self.click_button_by_id(selenium, 'buttonSaveWorkout')
        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Workouts')
        )

        # check shared link can no longer bew viewed
        self.logout(selenium)
        selenium.get(sharedLink)
        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.ID, 'errorIcon'), 'error')
        )

    def test_linked_planned_tour(self, server, selenium: WebDriver):
        self.login(selenium)
        self.__open_form(selenium)
        self.__fill_form(
            selenium,
            'My Workout',
            '2023-02-01',
            '15:30',
            22.5,
            1,
            13,
            46,
            123,
            650,
            plannedTourName='Megatour',
        )
        self.click_button_by_id(selenium, 'buttonSaveWorkout')

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Workouts')
        )

        assert len(selenium.find_elements(By.CSS_SELECTOR, 'section .card-body')) == 1

        # check number of linked workouts is shown
        selenium.get(self.build_url('/plannedTours'))
        pills = selenium.find_elements(By.CSS_SELECTOR, '.badge.rounded-pill.bg-orange')
        assert len(pills) == 1
        assert pills[0].text == '1 Workouts'

    def test_add_workout_from_fit_file(self, server, selenium: WebDriver):
        self.login(selenium)

        # open fit import modal
        selenium.get(self.build_url('/workouts'))

        selenium.find_element(By.CLASS_NAME, 'headline').find_element(By.TAG_NAME, 'a').click()
        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'New Workout')
        )

        buttons = selenium.find_elements(By.CSS_SELECTOR, 'section .btn')
        buttons[4].click()
        WebDriverWait(selenium, 5).until(
            expected_conditions.visibility_of_element_located((By.ID, 'buttonImportFromFitFile'))
        )

        # upload file
        dataDirectory = os.path.join(ROOT_DIRECTORY, 'sporttracker', 'dummyData')
        fitFilePath = os.path.join(dataDirectory, 'fitTrack_1.fit')
        selenium.find_element(By.ID, 'formFile').send_keys(fitFilePath)
        selenium.find_element(By.ID, 'buttonImportFromFitFile').click()

        # wait for form to open
        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'New Biking Workout')
        )

        # assert form is prefilled
        assert selenium.find_element(By.ID, 'workout-date').get_attribute('value') == '2024-09-20'
        assert selenium.find_element(By.ID, 'workout-time').get_attribute('value') == '16:30'
        assert selenium.find_element(By.ID, 'workout-distance').get_attribute('value') == '35.39'
        assert selenium.find_element(By.ID, 'workout-duration-hours').get_attribute('value') == '1'
        assert selenium.find_element(By.ID, 'workout-duration-minutes').get_attribute('value') == '25'
        assert selenium.find_element(By.ID, 'workout-duration-seconds').get_attribute('value') == '2'
        assert selenium.find_element(By.ID, 'workout-elevationSum').get_attribute('value') == '319'
        assert selenium.find_element(By.ID, 'workout-averageHeartRate').get_attribute('value') == ''

        # save
        selenium.find_element(By.ID, 'workout-name').send_keys('Import from FIT file')
        self.click_button_by_id(selenium, 'buttonSaveWorkout')

        # assert successful save
        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Workouts')
        )
        assert len(selenium.find_elements(By.CSS_SELECTOR, 'section .card-body')) == 1
