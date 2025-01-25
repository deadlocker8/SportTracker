import time

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait

from sporttracker.logic.model.SportType import SportType
from sporttracker.logic.model.User import create_user, Language
from tests.SeleniumTestBaseClass import SeleniumTestBaseClass
from tests.TestConstants import TEST_USERNAME, TEST_PASSWORD


@pytest.fixture(autouse=True)
def prepare_test_data(app):
    with app.app_context():
        create_user(TEST_USERNAME, TEST_PASSWORD, False, Language.ENGLISH)


class TestMaintenances(SeleniumTestBaseClass):
    def __open_maintenance_form(self, selenium):
        selenium.get(self.build_url('/maintenances'))

        selenium.find_element(By.CLASS_NAME, 'headline').find_element(By.TAG_NAME, 'a').click()
        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'New Maintenance'
            )
        )

    def __open_maintenance_edit_form(self, selenium):
        selenium.get(self.build_url('/maintenance/edit/1'))

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'Edit Maintenance'
            )
        )

    @staticmethod
    def __fill_maintenance_form(selenium, sportType, description, reminderLimit=None):
        select = Select(selenium.find_element(By.ID, 'maintenance-event-type'))
        select.select_by_visible_text(sportType.name.capitalize())

        descriptionInput = selenium.find_element(By.ID, 'maintenance-event-description')
        descriptionInput.clear()
        descriptionInput.send_keys(description)

        if reminderLimit is not None:
            if not selenium.find_element(
                By.ID, 'maintenance-event-reminder-checkbox'
            ).is_selected():
                selenium.find_element(
                    By.XPATH, '//label[@for="maintenance-event-reminder-checkbox"]'
                ).click()

            WebDriverWait(selenium, 5).until(
                expected_conditions.visibility_of_element_located(
                    (By.ID, 'maintenance-event-reminder-limit')
                )
            )

            reminderLimitInput = selenium.find_element(By.ID, 'maintenance-event-reminder-limit')
            reminderLimitInput.clear()
            reminderLimitInput.send_keys(reminderLimit)

    def __open_event_form(self, selenium):
        selenium.get(self.build_url('/maintenances'))

        selenium.find_element(By.CLASS_NAME, 'button-new-maintenance-event').click()
        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'New Maintenance Event'
            )
        )

    def __open_event_edit_form(self, selenium):
        selenium.get(self.build_url('/maintenanceEventInstances/edit/1'))

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'Edit Maintenance Event'
            )
        )

    @staticmethod
    def __fill_event_form(selenium, date, start_time):
        dateInput = selenium.find_element(By.ID, 'maintenance-event-date')
        dateInput.clear()
        dateInput.send_keys(date)

        timeInput = selenium.find_element(By.ID, 'maintenance-event-time')
        timeInput.clear()
        timeInput.send_keys(start_time)

    @staticmethod
    def __click_submit_button(selenium):
        button = selenium.find_element(By.CSS_SELECTOR, 'section form button')
        selenium.execute_script('arguments[0].scrollIntoView();', button)
        time.sleep(1)
        button.click()

    def test_add_maintenance_valid(self, server, selenium: WebDriver):
        self.login(selenium)
        self.__open_maintenance_form(selenium)
        self.__fill_maintenance_form(selenium, SportType.BIKING, 'chain oiled', '100')
        self.__click_submit_button(selenium)

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'Maintenance'
            )
        )

        assert len(selenium.find_elements(By.CSS_SELECTOR, 'section .card')) == 1

    def test_add_maintenance_all_empty(self, server, selenium: WebDriver):
        self.login(selenium)
        self.__open_maintenance_form(selenium)
        self.__fill_maintenance_form(selenium, SportType.BIKING, '')
        self.__click_submit_button(selenium)

        assert selenium.current_url.endswith('/maintenances/add')

    def test_edit_maintenance_valid(self, server, selenium: WebDriver):
        self.login(selenium)
        self.__open_maintenance_form(selenium)
        self.__fill_maintenance_form(selenium, SportType.BIKING, 'chain oiled', '500')
        self.__click_submit_button(selenium)

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'Maintenance'
            )
        )

        assert len(selenium.find_elements(By.CSS_SELECTOR, 'section .card')) == 1

        selenium.find_element(By.CLASS_NAME, 'button-edit-maintenance').click()
        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'Edit Maintenance'
            )
        )

        assert (
            selenium.find_element(By.ID, 'maintenance-event-description').get_attribute('value')
            == 'chain oiled'
        )

        self.__fill_maintenance_form(selenium, SportType.BIKING, 'chain replaced', '200')

        self.__click_submit_button(selenium)

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'Maintenance'
            )
        )

        assert len(selenium.find_elements(By.CSS_SELECTOR, 'section .card')) == 1

    def test_quick_filter_only_show_activated_sport_types(self, server, selenium: WebDriver):
        self.login(selenium)
        self.__open_maintenance_form(selenium)
        self.__fill_maintenance_form(selenium, SportType.BIKING, 'chain oiled')
        selenium.find_element(By.CSS_SELECTOR, 'section form button').click()

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'Maintenance'
            )
        )

        self.__open_maintenance_form(selenium)
        self.__fill_maintenance_form(selenium, SportType.RUNNING, 'new shoes')
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

    def test_add_event_valid(self, server, selenium: WebDriver):
        self.login(selenium)

        self.__open_maintenance_form(selenium)
        self.__fill_maintenance_form(selenium, SportType.BIKING, 'chain oiled')
        self.__click_submit_button(selenium)

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'Maintenance'
            )
        )

        assert len(selenium.find_elements(By.CSS_SELECTOR, 'section .card')) == 1

        self.__open_event_form(selenium)
        self.__fill_event_form(selenium, '2023-02-01', '15:30')
        selenium.find_element(By.CSS_SELECTOR, 'section form button').click()

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'Maintenance'
            )
        )

        assert len(selenium.find_elements(By.CLASS_NAME, 'timeline-icon')) == 2

    def test_add_event_all_empty(self, server, selenium: WebDriver):
        self.login(selenium)

        self.__open_maintenance_form(selenium)
        self.__fill_maintenance_form(selenium, SportType.BIKING, 'chain oiled')
        self.__click_submit_button(selenium)

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'Maintenance'
            )
        )

        assert len(selenium.find_elements(By.CSS_SELECTOR, 'section .card')) == 1

        self.__open_event_form(selenium)
        self.__fill_event_form(selenium, '', '')
        selenium.find_element(By.CSS_SELECTOR, 'section form button').click()

        assert selenium.current_url.endswith('/maintenanceEventInstances/add/1')

    def test_edit_event_valid(self, server, selenium: WebDriver, app):
        self.login(selenium)

        self.__open_maintenance_form(selenium)
        self.__fill_maintenance_form(selenium, SportType.BIKING, 'chain oiled')
        self.__click_submit_button(selenium)

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'Maintenance'
            )
        )

        assert len(selenium.find_elements(By.CSS_SELECTOR, 'section .card')) == 1

        self.__open_event_form(selenium)
        self.__fill_event_form(selenium, '2023-02-01', '15:30')
        selenium.find_element(By.CSS_SELECTOR, 'section form button').click()

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'Maintenance'
            )
        )

        self.__open_event_edit_form(selenium)

        assert (
            selenium.find_element(By.ID, 'maintenance-event-date').get_attribute('value')
            == '2023-02-01'
        )
        assert (
            selenium.find_element(By.ID, 'maintenance-event-time').get_attribute('value') == '15:30'
        )

        self.__fill_event_form(selenium, '2023-02-02', '16:30')
        selenium.find_element(By.CSS_SELECTOR, 'section form button[type="submit"]').click()

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'Maintenance'
            )
        )

        # actual event + pseudo element for "today"
        assert len(selenium.find_elements(By.CLASS_NAME, 'timeline-icon')) == 2

    def test_reminder_triggered(self, server, selenium: WebDriver):
        self.login(selenium)

        self.__open_maintenance_form(selenium)
        self.__fill_maintenance_form(selenium, SportType.BIKING, 'chain oiled', '0')
        self.__click_submit_button(selenium)

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'Maintenance'
            )
        )

        assert len(selenium.find_elements(By.CSS_SELECTOR, 'section .card')) == 1

        self.__open_event_form(selenium)
        self.__fill_event_form(selenium, '2023-02-01', '15:30')
        selenium.find_element(By.CSS_SELECTOR, 'section form button').click()

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'Maintenance'
            )
        )

        assert selenium.find_element(By.XPATH, '//span[contains(text(), "over limit")]')
