from datetime import datetime

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from sporttracker.bodyWeight.BodyWeightEntity import BodyWeight
from sporttracker.db import db
from sporttracker.user.UserEntity import create_user, Language, User
from tests.SeleniumTestBaseClass import SeleniumTestBaseClass
from tests.TestConstants import TEST_USERNAME, TEST_PASSWORD


@pytest.fixture(autouse=True)
def prepare_test_data(app):
    with app.app_context():
        create_user(TEST_USERNAME, TEST_PASSWORD, False, Language.ENGLISH, 2026)


def add_body_weight_entry(app, date: datetime, weight: int) -> None:
    with app.app_context():
        user = User.query.filter(User.username == TEST_USERNAME).first()
        db.session.add(BodyWeight(datetime=date, weight=weight, user_id=user.id))
        db.session.commit()


class TestBodyWeightOverview(SeleniumTestBaseClass):
    def test_body_weight_page_no_entries(self, server, selenium: WebDriver):
        self.login(selenium)
        selenium.get(self.build_url('/bodyWeight/'))

        assert 'Body Weight' in selenium.find_element(By.CLASS_NAME, 'headline-text').text

        sectionText = selenium.find_element(By.CSS_SELECTOR, 'section').text
        assert 'No body weight entries yet' in sectionText
        assert sectionText.count('- kg') == 4
        assert len(selenium.find_elements(By.CSS_SELECTOR, '.bmi-marker')) == 0

    def test_body_weight_page_with_entries(self, server, selenium: WebDriver, app):
        add_body_weight_entry(app, datetime(2024, 1, 1, 15, 0), 80000)
        add_body_weight_entry(app, datetime(2024, 1, 2, 15, 0), 80400)

        self.login(selenium)
        selenium.get(self.build_url('/bodyWeight/'))

        assert len(selenium.find_elements(By.CSS_SELECTOR, 'tbody tr')) == 2

        sectionText = selenium.find_element(By.CSS_SELECTOR, 'section').text
        assert '80.0 kg' in sectionText
        assert '80.4 kg' in sectionText
        assert '80.2 kg' in sectionText
        assert '+0.4 kg' in sectionText


class TestBodyWeightAdd(SeleniumTestBaseClass):
    def __open_add_form(self, selenium: WebDriver):
        self.login(selenium)
        selenium.get(self.build_url('/bodyWeight/add'))

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'New Body Weight Entry')
        )

    def test_add_body_weight_valid(self, server, selenium: WebDriver):
        self.__open_add_form(selenium)

        dateInput = selenium.find_element(By.ID, 'body-weight-date')
        dateInput.clear()
        dateInput.send_keys('2024-02-01')
        timeInput = selenium.find_element(By.ID, 'body-weight-time')
        timeInput.send_keys('15:30')
        selenium.find_element(By.ID, 'body-weight').send_keys('82.5')
        selenium.find_element(By.CSS_SELECTOR, 'section form button').click()

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Body Weight')
        )

        assert len(selenium.find_elements(By.CSS_SELECTOR, 'tbody tr')) == 1
        assert '82.5 kg' in selenium.find_element(By.CSS_SELECTOR, 'section').text

    def test_add_body_weight_all_empty(self, server, selenium: WebDriver):
        self.__open_add_form(selenium)

        selenium.find_element(By.CSS_SELECTOR, 'section form button').click()
        assert selenium.current_url.endswith('/bodyWeight/add')


class TestBodyWeightEdit(SeleniumTestBaseClass):
    def __open_edit_form(self, selenium: WebDriver):
        self.login(selenium)
        selenium.get(self.build_url('/bodyWeight/edit/1'))

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'Edit Body Weight Entry'
            )
        )

    def test_edit_body_weight_valid(self, server, selenium: WebDriver, app):
        add_body_weight_entry(app, datetime(2024, 1, 1, 15, 30), 80000)

        self.__open_edit_form(selenium)

        weightInput = selenium.find_element(By.ID, 'body-weight')
        weightInput.clear()
        weightInput.send_keys('81.0')
        selenium.find_element(By.CSS_SELECTOR, 'section form button').click()

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Body Weight')
        )

        assert len(selenium.find_elements(By.CSS_SELECTOR, 'tbody tr')) == 1
        assert '81.0 kg' in selenium.find_element(By.CSS_SELECTOR, 'section').text

    def test_edit_body_weight_delete_button_visible(self, server, selenium: WebDriver, app):
        add_body_weight_entry(app, datetime(2024, 1, 1, 15, 30), 80000)

        self.__open_edit_form(selenium)

        assert 'Delete' in selenium.find_element(By.CSS_SELECTOR, 'section').text


class TestBodyWeightDelete(SeleniumTestBaseClass):
    def test_delete_body_weight_entry(self, server, selenium: WebDriver, app):
        add_body_weight_entry(app, datetime(2024, 1, 1, 15, 30), 80000)

        self.login(selenium)
        selenium.get(self.build_url('/bodyWeight/'))

        selenium.find_element(By.CSS_SELECTOR, 'a[data-bs-toggle="modal"]').click()
        WebDriverWait(selenium, 5).until(
            expected_conditions.visibility_of_element_located((By.CSS_SELECTOR, '.button-delete-modal-action'))
        )
        selenium.find_element(By.CSS_SELECTOR, '.button-delete-modal-action').click()

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CSS_SELECTOR, 'section'), 'No body weight entries yet'
            )
        )
        assert len(selenium.find_elements(By.CSS_SELECTOR, 'tbody tr')) == 0


class TestBodyWeightBmi(SeleniumTestBaseClass):
    @staticmethod
    def __set_height(app, height: int) -> None:
        with app.app_context():
            user = User.query.filter(User.username == TEST_USERNAME).first()
            user.height = height
            db.session.commit()

    def test_body_weight_shows_bmi_when_height_set(self, server, selenium: WebDriver, app):
        self.__set_height(app, 180)
        add_body_weight_entry(app, datetime(2024, 1, 1, 15, 30), 80000)

        self.login(selenium)
        selenium.get(self.build_url('/bodyWeight/'))

        sectionText = selenium.find_element(By.CSS_SELECTOR, 'section').text
        assert 'BMI' in sectionText
        assert '24.7' in sectionText
        assert len(selenium.find_elements(By.CSS_SELECTOR, '.bmi-marker')) == 1
