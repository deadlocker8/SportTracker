import time

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait

from sporttracker.logic.model.TrackType import TrackType
from sporttracker.logic.model.User import create_user, Language
from tests.SeleniumTestBaseClass import SeleniumTestBaseClass
from tests.TestConstants import TEST_USERNAME, TEST_PASSWORD


@pytest.fixture(autouse=True)
def prepare_test_data(app):
    with app.app_context():
        create_user(TEST_USERNAME, TEST_PASSWORD, False, Language.ENGLISH)


class TestMaintenanceEvents(SeleniumTestBaseClass):
    def __open_form(self, selenium):
        selenium.get(self.build_url('/maintenanceEvents'))

        selenium.find_element(By.CLASS_NAME, 'headline').find_element(By.TAG_NAME, 'a').click()
        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'New Maintenance Event'
            )
        )

    def __open_edit_form(self, selenium):
        selenium.get(self.build_url('/maintenanceEvents/edit/1'))

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'Edit Maintenance Event'
            )
        )

    @staticmethod
    def __fill_form(selenium, trackType, date, startTime, description):
        select = Select(selenium.find_element(By.ID, 'maintenance-event-type'))
        select.select_by_visible_text(trackType.name.capitalize())
        dateInput = selenium.find_element(By.ID, 'maintenance-event-date')
        dateInput.clear()
        dateInput.send_keys(date)

        timeInput = selenium.find_element(By.ID, 'maintenance-event-time')
        timeInput.clear()
        timeInput.send_keys(startTime)

        descriptionInput = selenium.find_element(By.ID, 'maintenance-event-description')
        descriptionInput.clear()
        descriptionInput.send_keys(description)

    def __click_submit_button(self, selenium):
        button = selenium.find_element(By.CSS_SELECTOR, 'section form button')
        selenium.execute_script('arguments[0].scrollIntoView();', button)
        time.sleep(1)
        button.click()

    def test_add_event_valid(self, server, selenium: WebDriver):
        self.login(selenium)
        self.__open_form(selenium)
        self.__fill_form(selenium, TrackType.BIKING, '2023-02-01', '15:30', 'chain oiled')
        selenium.find_element(By.CSS_SELECTOR, 'section form button').click()

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'Maintenance'
            )
        )

        assert len(selenium.find_elements(By.CSS_SELECTOR, 'section .card')) == 1

    def test_add_event_all_empty(self, server, selenium: WebDriver):
        self.login(selenium)
        self.__open_form(selenium)
        self.__fill_form(selenium, TrackType.BIKING, '', '', '')
        selenium.find_element(By.CSS_SELECTOR, 'section form button').click()

        assert selenium.current_url.endswith('/maintenanceEvents/add')

    def test_quick_filter_only_show_activated_track_types(self, server, selenium: WebDriver):
        self.login(selenium)
        self.__open_form(selenium)
        self.__fill_form(selenium, TrackType.BIKING, '2023-02-01', '15:30', 'chain oiled')
        selenium.find_element(By.CSS_SELECTOR, 'section form button').click()

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'Maintenance'
            )
        )

        self.__open_form(selenium)
        self.__fill_form(selenium, TrackType.RUNNING, '2023-02-01', '15:30', 'new shoes')
        selenium.find_element(By.CSS_SELECTOR, 'section form button').click()

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'Maintenance'
            )
        )

        selenium.find_elements(By.CLASS_NAME, 'quick-filter')[0].click()

        WebDriverWait(selenium, 5).until(
            expected_conditions.invisibility_of_element_located(
                (By.XPATH, '//h4[text()="New Maintenance Event"]')
            )
        )

        assert len(selenium.find_elements(By.CSS_SELECTOR, 'section .card')) == 1

    def test_edit_event_valid(self, server, selenium: WebDriver, app):
        self.login(selenium)
        self.__open_form(selenium)
        self.__fill_form(selenium, TrackType.BIKING, '2023-02-01', '15:30', 'chain oiled')
        selenium.find_element(By.CSS_SELECTOR, 'section form button').click()

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'Maintenance'
            )
        )

        self.__open_edit_form(selenium)

        assert (
            selenium.find_element(By.ID, 'maintenance-event-date').get_attribute('value')
            == '2023-02-01'
        )
        assert (
            selenium.find_element(By.ID, 'maintenance-event-time').get_attribute('value') == '15:30'
        )
        assert (
            selenium.find_element(By.ID, 'maintenance-event-description').get_attribute('value')
            == 'chain oiled'
        )

        self.__fill_form(selenium, TrackType.BIKING, '2023-02-02', '16:30', 'chain replaced')
        selenium.find_element(By.CSS_SELECTOR, 'section form button[type="submit"]').click()

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'Maintenance'
            )
        )

        assert len(selenium.find_elements(By.CLASS_NAME, 'maintenance-event-description')) == 1
