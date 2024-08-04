import time
from datetime import datetime

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait

from sporttracker.logic.model.CustomTrackField import CustomTrackField, CustomTrackFieldType
from sporttracker.logic.model.Participant import Participant
from sporttracker.logic.model.PlannedTour import PlannedTour, TravelType, TravelDirection
from sporttracker.logic.model.TrackType import TrackType
from sporttracker.logic.model.User import create_user, Language, User
from sporttracker.logic.model.db import db
from tests.SeleniumTestBaseClass import SeleniumTestBaseClass
from tests.TestConstants import TEST_USERNAME, TEST_PASSWORD


@pytest.fixture(autouse=True)
def prepare_test_data(app):
    with app.app_context():
        user = create_user(TEST_USERNAME, TEST_PASSWORD, False, Language.ENGLISH)

        plannedTour = PlannedTour(
            id=1,
            type=TrackType.BIKING,
            name='Megatour',
            creation_date=datetime.now(),
            last_edit_date=datetime.now(),
            last_edit_user_id=user.id,
            gpxFileName=None,
            user_id=user.id,
            shared_users=[],
            arrival_method=TravelType.TRAIN,
            departure_method=TravelType.NONE,
            direction=TravelDirection.SINGLE,
            share_code=None,
        )
        db.session.add(plannedTour)
        db.session.commit()


class TestTracks(SeleniumTestBaseClass):
    def __open_form(self, selenium, buttonIndex=0, expectedHeadline='New Biking Track'):
        selenium.get(self.build_url('/tracks'))

        selenium.find_element(By.CLASS_NAME, 'headline').find_element(By.TAG_NAME, 'a').click()
        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'New Track'
            )
        )

        buttons = selenium.find_elements(By.CSS_SELECTOR, 'section .btn')
        buttons[buttonIndex].click()
        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), expectedHeadline
            )
        )

    def __open_edit_form(self, selenium):
        selenium.get(self.build_url('/tracks/edit/1'))

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'Edit Biking Track'
            )
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
        selenium.find_element(By.ID, 'track-name').send_keys(name)
        selenium.find_element(By.ID, 'track-date').send_keys(date)
        selenium.find_element(By.ID, 'track-time').send_keys(startTime)
        selenium.find_element(By.ID, 'track-distance').send_keys(distance)
        selenium.find_element(By.ID, 'track-duration-hours').send_keys(hours)
        selenium.find_element(By.ID, 'track-duration-minutes').send_keys(minutes)
        selenium.find_element(By.ID, 'track-duration-seconds').send_keys(seconds)
        selenium.find_element(By.ID, 'track-averageHeartRate').send_keys(averageHeartRate)
        selenium.find_element(By.ID, 'track-elevationSum').send_keys(elevationSum)

        select = Select(selenium.find_element(By.ID, 'track-plannedTour'))
        select.select_by_visible_text(plannedTourName)

    def test_add_track_valid(self, server, selenium: WebDriver):
        self.login(selenium)
        self.__open_form(selenium)
        self.__fill_form(selenium, 'My Track', '2023-02-01', '15:30', 22.5, 1, 13, 46, 123, 650)
        self.click_button_by_id(selenium, 'buttonSaveTrack')

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'Tracks'
            )
        )

        assert len(selenium.find_elements(By.CSS_SELECTOR, 'section .card-body')) == 1

    def test_add_track_all_empty(self, server, selenium: WebDriver):
        self.login(selenium)
        self.__open_form(selenium)
        self.__fill_form(selenium, '', '', '', '', '', '', '', '', '')
        self.click_button_by_id(selenium, 'buttonSaveTrack')

        assert selenium.current_url.endswith('/tracks/add/BIKING')

    def test_add_track_mandatory_custom_field_not_filled(self, server, selenium: WebDriver, app):
        user = User.query.filter(User.username == TEST_USERNAME).first()

        with app.app_context():
            customTrackField = CustomTrackField(
                type=CustomTrackFieldType.INTEGER,
                track_type=TrackType.BIKING,
                name='my_custom_field',
                is_required=True,
                user_id=user.id,
            )
            db.session.add(customTrackField)
            db.session.commit()

        self.login(selenium)
        self.__open_form(selenium)
        self.__fill_form(selenium, 'My Track', '2023-02-01', '15:30', 22.5, 1, 13, 46, 123, 650)
        self.click_button_by_id(selenium, 'buttonSaveTrack')

        assert selenium.current_url.endswith('/tracks/add/BIKING')

    def test_add_track_mandatory_custom_field_filled(self, server, selenium: WebDriver, app):
        user = User.query.filter(User.username == TEST_USERNAME).first()

        with app.app_context():
            customTrackField = CustomTrackField(
                type=CustomTrackFieldType.INTEGER,
                track_type=TrackType.BIKING,
                name='my_custom_field',
                is_required=True,
                user_id=user.id,
            )
            db.session.add(customTrackField)
            db.session.commit()

        self.login(selenium)
        self.__open_form(selenium)
        self.__fill_form(selenium, 'My Track', '2023-02-01', '15:30', 22.5, 1, 13, 46, 123, 650)
        selenium.find_element(By.ID, 'track-my_custom_field').send_keys('15')
        self.click_button_by_id(selenium, 'buttonSaveTrack')

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'Tracks'
            )
        )

        assert len(selenium.find_elements(By.CSS_SELECTOR, 'section .card-body')) == 1

    def test_add_track_non_mandatory_custom_field_not_filled(
        self, server, selenium: WebDriver, app
    ):
        user = User.query.filter(User.username == TEST_USERNAME).first()

        with app.app_context():
            customTrackField = CustomTrackField(
                type=CustomTrackFieldType.INTEGER,
                track_type=TrackType.BIKING,
                name='my_custom_field',
                is_required=False,
                user_id=user.id,
            )
            db.session.add(customTrackField)
            db.session.commit()

        self.login(selenium)
        self.__open_form(selenium)
        self.__fill_form(selenium, 'My Track', '2023-02-01', '15:30', 22.5, 1, 13, 46, 123, 650)
        self.click_button_by_id(selenium, 'buttonSaveTrack')

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'Tracks'
            )
        )

        assert len(selenium.find_elements(By.CSS_SELECTOR, 'section .card-body')) == 1

    def test_add_track_one_participant_selected(self, server, selenium: WebDriver, app):
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
        self.__fill_form(selenium, 'My Track', '2023-02-01', '15:30', 22.5, 1, 13, 46, 123, 650)
        selenium.find_element(By.XPATH, '//label[@for="participant-1"]').click()
        self.click_button_by_id(selenium, 'buttonSaveTrack')

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'Tracks'
            )
        )

        cards = selenium.find_elements(By.CSS_SELECTOR, 'section .card-body')
        assert len(cards) == 1
        # check participants icon is displayed
        assert cards[0].find_element(By.XPATH, '//span[text()="group"]')

    def test_add_track_multiple_participant_selected(self, server, selenium: WebDriver, app):
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
        self.__fill_form(selenium, 'My Track', '2023-02-01', '15:30', 22.5, 1, 13, 46, 123, 650)
        selenium.find_element(By.XPATH, '//label[@for="participant-1"]').click()
        selenium.find_element(By.XPATH, '//label[@for="participant-2"]').click()
        self.click_button_by_id(selenium, 'buttonSaveTrack')

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'Tracks'
            )
        )

        cards = selenium.find_elements(By.CSS_SELECTOR, 'section .card-body')
        assert len(cards) == 1
        # check participants icon is displayed
        assert cards[0].find_element(By.XPATH, '//span[text()="group"]')

    def test_quick_filter_only_show_activated_track_types(self, server, selenium: WebDriver):
        self.login(selenium)
        self.__open_form(selenium)
        self.__fill_form(
            selenium, 'My Biking Track', '2023-02-01', '15:30', 22.5, 1, 13, 46, 123, 650
        )
        self.click_button_by_id(selenium, 'buttonSaveTrack')

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'Tracks'
            )
        )

        self.__open_form(selenium, buttonIndex=1, expectedHeadline='New Running Track')
        self.__fill_form(
            selenium, 'My Running Track', '2023-02-01', '16:30', 5.5, 0, 20, 12, 188, 15
        )
        self.click_button_by_id(selenium, 'buttonSaveTrack')

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'Tracks'
            )
        )

        selenium.find_elements(By.CLASS_NAME, 'quick-filter')[0].click()

        WebDriverWait(selenium, 5).until(
            expected_conditions.invisibility_of_element_located(
                (By.XPATH, '//h4[text()="New Biking Track"]')
            )
        )

        assert len(selenium.find_elements(By.CSS_SELECTOR, 'section .card-body')) == 1

    def test_month_select(self, server, selenium: WebDriver):
        self.login(selenium)

        selenium.find_element(By.CSS_SELECTOR, '#month-select').click()
        WebDriverWait(selenium, 5).until(
            expected_conditions.visibility_of_element_located((By.ID, 'headline-years'))
        )

        yearButton = selenium.find_elements(By.CLASS_NAME, 'btn-select-year')[0]
        year = yearButton.get_attribute('data-year')
        yearButton.click()
        WebDriverWait(selenium, 5).until(
            expected_conditions.visibility_of_element_located((By.ID, 'headline-months'))
        )

        monthIndex = 4
        selenium.find_elements(By.CLASS_NAME, 'btn-select-month')[monthIndex].click()
        WebDriverWait(selenium, 5).until(
            expected_conditions.invisibility_of_element_located((By.ID, 'headline-months'))
        )

        assert selenium.current_url.endswith(f'/tracks/{year}/{monthIndex + 1}')

    def test_new_track_share_via_link(self, server, selenium: WebDriver):
        self.login(selenium)
        self.__open_form(selenium)

        self.__fill_form(
            selenium, 'My Biking Track', '2023-02-01', '15:30', 22.5, 1, 13, 46, 123, 650
        )

        self.click_button_by_id(selenium, 'buttonCreateSharedLink')
        WebDriverWait(selenium, 5).until(
            expected_conditions.visibility_of_element_located((By.ID, 'sharedLink'))
        )
        sharedLink = selenium.find_element(By.ID, 'sharedLink').text
        self.click_button_by_id(selenium, 'buttonSaveTrack')

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'Tracks'
            )
        )

        cards = selenium.find_elements(By.CSS_SELECTOR, 'section .card')
        assert len(cards) == 1
        # check share icon is displayed
        assert cards[0].find_element(By.XPATH, '//span[contains(text(), "share")]')

        # check shared link can be viewed without login
        self.logout(selenium)
        selenium.get(sharedLink)
        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'planned-tour-name'), 'My Biking Track'
            )
        )

    def test_edit_track_remove_shared_link(self, server, selenium: WebDriver):
        self.login(selenium)
        self.__open_form(selenium)

        self.__fill_form(
            selenium, 'My Biking Track', '2023-02-01', '15:30', 22.5, 1, 13, 46, 123, 650
        )

        self.click_button_by_id(selenium, 'buttonCreateSharedLink')
        WebDriverWait(selenium, 5).until(
            expected_conditions.visibility_of_element_located((By.ID, 'sharedLink'))
        )
        sharedLink = selenium.find_element(By.ID, 'sharedLink').text
        self.click_button_by_id(selenium, 'buttonSaveTrack')

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'Tracks'
            )
        )

        self.__open_edit_form(selenium)

        buttonSharedLinkDeleteModal = selenium.find_element(By.ID, 'buttonSharedLinkDeleteModal')
        selenium.execute_script('arguments[0].scrollIntoView();', buttonSharedLinkDeleteModal)
        time.sleep(1)
        buttonSharedLinkDeleteModal.click()
        WebDriverWait(selenium, 5).until(
            expected_conditions.element_to_be_clickable((By.ID, 'buttonSharedLinkDelete'))
        )
        time.sleep(1)
        selenium.find_element(By.ID, 'buttonSharedLinkDelete').click()
        WebDriverWait(selenium, 5).until(
            expected_conditions.invisibility_of_element_located((By.ID, 'sharedLink'))
        )
        self.click_button_by_id(selenium, 'buttonSaveTrack')
        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'Tracks'
            )
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
            'My Track',
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
        self.click_button_by_id(selenium, 'buttonSaveTrack')

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'Tracks'
            )
        )

        assert len(selenium.find_elements(By.CSS_SELECTOR, 'section .card-body')) == 1

        # check number of linked tracks is shown
        selenium.get(self.build_url('/plannedTours'))
        pills = selenium.find_elements(By.CSS_SELECTOR, '.badge.rounded-pill.bg-orange')
        assert len(pills) == 1
        assert pills[0].text == '1 Tracks'
