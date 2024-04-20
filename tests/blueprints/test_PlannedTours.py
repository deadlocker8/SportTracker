import time

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait

from sporttracker.logic.model.Track import TrackType
from sporttracker.logic.model.User import create_user, Language
from tests.SeleniumTestBaseClass import SeleniumTestBaseClass
from tests.TestConstants import TEST_USERNAME, TEST_PASSWORD


@pytest.fixture(autouse=True)
def prepare_test_data(app):
    with app.app_context():
        create_user(TEST_USERNAME, TEST_PASSWORD, False, Language.ENGLISH)


class TestPlannedTours(SeleniumTestBaseClass):
    def __open_form(self, selenium):
        selenium.get(self.build_url('/plannedTours'))

        selenium.find_element(By.CLASS_NAME, 'headline').find_element(By.TAG_NAME, 'a').click()
        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'New Planned Tour'
            )
        )

    def __open_edit_form(self, selenium):
        selenium.get(self.build_url('/plannedTours/edit/1'))

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'Edit Planned Tour'
            )
        )

    @staticmethod
    def __fill_form(selenium, trackType, name):
        select = Select(selenium.find_element(By.ID, 'planned-tour-type'))
        select.select_by_visible_text(trackType.name.capitalize())

        nameInput = selenium.find_element(By.ID, 'planned-tour-name')
        nameInput.clear()
        nameInput.send_keys(name)

    def __click_submit_button(self, selenium):
        button = selenium.find_element(By.CSS_SELECTOR, 'section form button')
        selenium.execute_script('arguments[0].scrollIntoView();', button)
        time.sleep(1)
        button.click()

    def test_add_tour_valid(self, server, selenium: WebDriver):
        self.login(selenium)
        self.__open_form(selenium)
        self.__fill_form(selenium, TrackType.BIKING, 'Awesome Tour')
        selenium.find_element(By.CSS_SELECTOR, 'section form button').click()

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'Planned Tours'
            )
        )

        assert len(selenium.find_elements(By.CSS_SELECTOR, 'section .card')) == 1

    def test_add_tour_all_empty(self, server, selenium: WebDriver):
        self.login(selenium)
        self.__open_form(selenium)
        self.__fill_form(selenium, TrackType.BIKING, '')
        selenium.find_element(By.CSS_SELECTOR, 'section form button').click()

        assert selenium.current_url.endswith('/plannedTours/add')

    def test_quick_filter_only_show_activated_track_types(self, server, selenium: WebDriver):
        self.login(selenium)
        self.__open_form(selenium)
        self.__fill_form(selenium, TrackType.BIKING, 'Awesome Tour')
        selenium.find_element(By.CSS_SELECTOR, 'section form button').click()

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'Planned Tours'
            )
        )

        self.__open_form(selenium)
        self.__fill_form(selenium, TrackType.RUNNING, 'Run away')
        selenium.find_element(By.CSS_SELECTOR, 'section form button').click()

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'Planned Tours'
            )
        )

        selenium.find_elements(By.CLASS_NAME, 'quick-filter')[0].click()

        WebDriverWait(selenium, 5).until(
            expected_conditions.invisibility_of_element_located(
                (By.XPATH, '//h4[text()="New Planned Tour"]')
            )
        )

        assert len(selenium.find_elements(By.CSS_SELECTOR, 'section .card')) == 1

    def test_edit_tour_valid(self, server, selenium: WebDriver, app):
        self.login(selenium)
        self.__open_form(selenium)
        self.__fill_form(selenium, TrackType.BIKING, 'Awesome Tour')
        selenium.find_element(By.CSS_SELECTOR, 'section form button').click()

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'Planned Tours'
            )
        )

        self.__open_edit_form(selenium)

        assert (
            selenium.find_element(By.ID, 'planned-tour-name').get_attribute('value')
            == 'Awesome Tour'
        )

        self.__fill_form(selenium, TrackType.BIKING, 'Better Tour')
        selenium.find_element(By.CSS_SELECTOR, 'section form button[type="submit"]').click()

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'Planned Tours'
            )
        )

        assert len(selenium.find_elements(By.CLASS_NAME, 'planned-tour-name')) == 1
