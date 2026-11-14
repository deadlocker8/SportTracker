import os
import time
from datetime import date, datetime

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait

from sporttracker.db import db
from sporttracker.equipment.bike.BikeEntity import Bike
from sporttracker.equipment.clothes.ClothesEntity import Clothes
from sporttracker.equipment.clothes.ClothesType import ClothesType
from sporttracker.equipment.custom.CustomEquipmentEntity import CustomEquipment
from sporttracker.equipment.presets.EquipmentPresetService import EquipmentPresetService
from sporttracker.plannedTour.PlannedTourEntity import PlannedTour
from sporttracker.plannedTour.TravelDirection import TravelDirection
from sporttracker.plannedTour.TravelType import TravelType
from sporttracker.user.CustomWorkoutFieldEntity import CustomWorkoutField, CustomWorkoutFieldType
from sporttracker.user.ParticipantEntity import Participant
from sporttracker.user.UserEntity import Language, User, create_user
from sporttracker.workout.WorkoutType import WorkoutType
from tests.SeleniumTestBaseClass import SeleniumTestBaseClass
from tests.TestConstants import ROOT_DIRECTORY, TEST_PASSWORD, TEST_USERNAME


@pytest.fixture(autouse=True)
def prepare_test_data(app):
    with app.app_context():
        user = create_user(TEST_USERNAME, TEST_PASSWORD, False, Language.ENGLISH, 2026)

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
        db.session.add(
            Bike(
                name='My Bike',
                workout_type=WorkoutType.BIKING,
                purchase_date=date(2020, 1, 1),
                is_active=True,
                user_id=user.id,
            )
        )
        db.session.add(
            Clothes(
                name='My Clothes',
                workout_type=WorkoutType.BIKING,
                purchase_date=date(2021, 1, 1),
                clothes_type=ClothesType.TOPS,
                is_active=True,
                user_id=user.id,
            )
        )
        db.session.add(
            CustomEquipment(
                name='My Inactive Equipment',
                workout_type=WorkoutType.BIKING,
                purchase_date=date(2022, 1, 1),
                is_active=False,
                user_id=user.id,
            )
        )
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

    @staticmethod
    def __submit_equipment_modal(selenium):
        selenium.find_element(
            By.XPATH,
            '//div[@id="workout-equipment-modal"]//button[text()="Apply"]',
        ).click()
        WebDriverWait(selenium, 5).until(
            expected_conditions.invisibility_of_element_located((By.ID, 'workout-equipment-modal'))
        )

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

    def test_add_and_edit_workout_with_equipment(self, server, selenium: WebDriver, app):
        with app.app_context():
            bike_id = Bike.query.filter(Bike.name == 'My Bike').first().id
            clothes_id = Clothes.query.filter(Clothes.name == 'My Clothes').first().id
            inactive_equipment_id = (
                CustomEquipment.query.filter(CustomEquipment.name == 'My Inactive Equipment').first().id
            )

        self.login(selenium)
        self.__open_form(selenium)
        self.__fill_form(selenium, 'My Workout', '2023-02-01', '15:30', 22.5, 1, 13, 46, 123, 650)

        buttonEditEquipment = selenium.find_element(By.ID, 'buttonWorkoutEquipmentEdit')
        selenium.execute_script('arguments[0].scrollIntoView();', buttonEditEquipment)
        time.sleep(1)
        buttonEditEquipment.click()

        bike_card_selector = f'.equipment-modal-card[data-equipment-id="{bike_id}"]'
        clothes_card_selector = f'.equipment-modal-card[data-equipment-id="{clothes_id}"]'
        inactive_card_selector = f'.equipment-modal-card[data-equipment-id="{inactive_equipment_id}"]'

        WebDriverWait(selenium, 5).until(
            expected_conditions.visibility_of_element_located((By.CSS_SELECTOR, bike_card_selector))
        )
        assert not selenium.find_elements(By.CSS_SELECTOR, inactive_card_selector)
        assert selenium.find_elements(By.CSS_SELECTOR, '#workout-equipment-modal .equipment-group-placeholder')

        selected_count = selenium.find_element(By.ID, 'workout-equipment-selected-count')
        assert selected_count.text == '0'

        bike_card = selenium.find_element(By.CSS_SELECTOR, bike_card_selector)
        selenium.execute_script('arguments[0].click();', bike_card)

        bike_select_icon = selenium.find_element(By.CSS_SELECTOR, f'{bike_card_selector} .equipment-select-icon')
        assert bike_select_icon.get_attribute('data-selected') == 'true'

        selenium.execute_script('arguments[0].click();', bike_card)
        assert bike_select_icon.get_attribute('data-selected') == 'false'
        assert selected_count.text == '0'

        selenium.execute_script('arguments[0].click();', bike_card)
        assert bike_select_icon.get_attribute('data-selected') == 'true'

        selenium.execute_script(
            'arguments[0].click();',
            selenium.find_element(By.CSS_SELECTOR, clothes_card_selector),
        )
        clothes_select_icon = selenium.find_element(By.CSS_SELECTOR, f'{clothes_card_selector} .equipment-select-icon')
        assert clothes_select_icon.get_attribute('data-selected') == 'true'
        assert selected_count.text == '2'
        assert not selenium.find_elements(By.CSS_SELECTOR, '#workout-equipment-chips')

        self.__submit_equipment_modal(selenium)

        assert selenium.find_element(By.ID, 'workout-equipment-selected-count').text == '2'
        self.click_button_by_id(selenium, 'buttonSaveWorkout')

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Workouts')
        )

    def test_add_workout_with_equipment_preset_deselects_other_equipment(self, server, selenium: WebDriver, app):
        with app.app_context():
            user = User.query.filter(User.username == TEST_USERNAME).first()
            bike_id = Bike.query.filter(Bike.name == 'My Bike').first().id
            clothes_id = Clothes.query.filter(Clothes.name == 'My Clothes').first().id

            EquipmentPresetService.add('Bike only', WorkoutType.BIKING, [bike_id], user.id)

        self.login(selenium)
        self.__open_form(selenium)
        self.__fill_form(selenium, 'My Workout', '2023-02-01', '15:30', 22.5, 1, 13, 46, 123, 650)

        buttonEditEquipment = selenium.find_element(By.ID, 'buttonWorkoutEquipmentEdit')
        selenium.execute_script('arguments[0].scrollIntoView();', buttonEditEquipment)
        time.sleep(1)
        buttonEditEquipment.click()

        bike_card_selector = f'.equipment-modal-card[data-equipment-id="{bike_id}"]'
        clothes_card_selector = f'.equipment-modal-card[data-equipment-id="{clothes_id}"]'

        WebDriverWait(selenium, 5).until(
            expected_conditions.visibility_of_element_located((By.CSS_SELECTOR, bike_card_selector))
        )

        # manually select equipment that is not part of the preset
        selenium.execute_script(
            'arguments[0].click();',
            selenium.find_element(By.CSS_SELECTOR, clothes_card_selector),
        )

        clothes_select_icon = selenium.find_element(By.CSS_SELECTOR, f'{clothes_card_selector} .equipment-select-icon')
        assert clothes_select_icon.get_attribute('data-selected') == 'true'
        assert selenium.find_element(By.ID, 'workout-equipment-selected-count').text == '1'

        # apply the preset
        selenium.find_element(By.ID, 'workout-equipment-presets-dropdown').click()
        preset_button = selenium.find_element(By.CSS_SELECTOR, '.workout-equipment-preset')
        WebDriverWait(selenium, 5).until(expected_conditions.element_to_be_clickable(preset_button))
        selenium.execute_script('arguments[0].click();', preset_button)

        bike_select_icon = selenium.find_element(By.CSS_SELECTOR, f'{bike_card_selector} .equipment-select-icon')
        assert bike_select_icon.get_attribute('data-selected') == 'true'
        assert clothes_select_icon.get_attribute('data-selected') == 'false'
        assert selenium.find_element(By.ID, 'workout-equipment-selected-count').text == '1'

        hidden_inputs = selenium.find_elements(
            By.CSS_SELECTOR, '#workout-equipment-hidden-inputs input[name="equipment_ids"]'
        )
        assert {hidden_input.get_attribute('value') for hidden_input in hidden_inputs} == {str(bike_id)}

        self.__submit_equipment_modal(selenium)

        assert selenium.find_element(By.ID, 'workout-equipment-selected-count').text == '1'
        self.click_button_by_id(selenium, 'buttonSaveWorkout')

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Workouts')
        )

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
