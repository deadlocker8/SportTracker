import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from sporttracker.user.ParticipantEntity import Participant
from sporttracker.user.UserEntity import create_user, Language, User
from sporttracker.logic.model.db import db
from tests.SeleniumTestBaseClass import SeleniumTestBaseClass
from tests.TestConstants import TEST_USERNAME, TEST_PASSWORD


@pytest.fixture(autouse=True)
def prepare_test_data(app):
    with app.app_context():
        create_user(TEST_USERNAME, TEST_PASSWORD, False, Language.ENGLISH)


class TestParticipants(SeleniumTestBaseClass):
    def __open_add_form(self, selenium):
        self.login(selenium)
        selenium.get(self.build_url('/settings/participants/add'))

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'New Participant')
        )

    def __open_edit_form(self, selenium):
        self.login(selenium)
        selenium.get(self.build_url('/settings/participants/edit/1'))

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Edit Participant')
        )

    def __create_participant(self, app, name):
        user = User.query.filter(User.username == TEST_USERNAME).first()
        with app.app_context():
            participant = Participant(name=name, user_id=user.id)
            db.session.add(participant)
            db.session.commit()

    def test_add_participant_valid(self, server, selenium: WebDriver):
        self.__open_add_form(selenium)

        selenium.find_element(By.ID, 'participant-name').send_keys('John Doe')
        selenium.find_element(By.CSS_SELECTOR, 'section form button').click()

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Settings')
        )

        assert len(selenium.find_elements(By.XPATH, '//td[text()="John Doe"]')) == 1

    def test_add_participant_name_already_used(self, server, selenium: WebDriver, app):
        self.__create_participant(app, 'John Doe')
        self.__open_add_form(selenium)

        selenium.find_element(By.ID, 'participant-name').send_keys('John Doe')
        selenium.find_element(By.CSS_SELECTOR, 'section form button').click()

        assert selenium.current_url.endswith('/settings/participants/add')
        assert selenium.find_element(By.CLASS_NAME, 'alert-danger') is not None

    def test_edit_participant_valid(self, server, selenium: WebDriver, app):
        self.__create_participant(app, 'John Doe')
        self.__open_edit_form(selenium)

        selenium.find_element(By.ID, 'participant-name').clear()
        selenium.find_element(By.ID, 'participant-name').send_keys('Jane')
        selenium.find_element(By.CSS_SELECTOR, 'section form button').click()

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Settings')
        )

        assert len(selenium.find_elements(By.XPATH, '//td[text()="Jane"]')) == 1

    def test_edit_participant_name_already_used(self, server, selenium: WebDriver, app):
        self.__create_participant(app, 'John Doe')
        self.__create_participant(app, 'Jane')
        self.__open_edit_form(selenium)

        selenium.find_element(By.ID, 'participant-name').clear()
        selenium.find_element(By.ID, 'participant-name').send_keys('Jane')
        selenium.find_element(By.CSS_SELECTOR, 'section form button').click()

        assert selenium.current_url.endswith('/settings/participants/edit/1')
        assert selenium.find_element(By.CLASS_NAME, 'alert-danger') is not None
