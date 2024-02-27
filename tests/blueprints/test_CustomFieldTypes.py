import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from sporttracker.logic.model.CustomTrackField import (
    CustomTrackField,
    CustomTrackFieldType,
    RESERVED_FIELD_NAMES,
)
from sporttracker.logic.model.Track import TrackType
from sporttracker.logic.model.User import create_user, Language, User
from sporttracker.logic.model.db import db
from tests.SeleniumTestBaseClass import SeleniumTestBaseClass
from tests.TestConstants import TEST_USERNAME, TEST_PASSWORD


@pytest.fixture(autouse=True)
def prepare_test_data(app):
    with app.app_context():
        create_user(TEST_USERNAME, TEST_PASSWORD, False, Language.ENGLISH)


class TestCustomFieldTypes(SeleniumTestBaseClass):
    def __open_add_form(self, selenium):
        self.login(selenium)
        selenium.get(self.build_url('/settings/customFields/add/BIKING'))

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.TAG_NAME, 'h1'), 'New Custom Track Field'
            )
        )

    def __open_edit_form(self, selenium):
        self.login(selenium)
        selenium.get(self.build_url('/settings/customFields/edit/1'))

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.TAG_NAME, 'h1'), 'Edit Custom Track Field'
            )
        )

    def __create_custom_field(self, app, name):
        user = User.query.filter(User.username == TEST_USERNAME).first()
        with app.app_context():
            customTrackField = CustomTrackField(
                type=CustomTrackFieldType.INTEGER,
                track_type=TrackType.BIKING,
                name=name,
                is_required=False,
                user_id=user.id,
            )
            db.session.add(customTrackField)
            db.session.commit()

    def test_add_custom_track_field_valid(self, server, selenium: WebDriver):
        self.__open_add_form(selenium)

        selenium.find_element(By.ID, 'field-name').send_keys('my_custom_field')
        selenium.find_element(By.CSS_SELECTOR, 'section form button').click()

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.TAG_NAME, 'h1'), 'Settings')
        )

        assert len(selenium.find_elements(By.XPATH, '//td[text()="STRING"]')) == 1

    def test_add_custom_track_field_reserved_name(self, server, selenium: WebDriver):
        self.__open_add_form(selenium)

        selenium.find_element(By.ID, 'field-name').send_keys(RESERVED_FIELD_NAMES[0])
        selenium.find_element(By.CSS_SELECTOR, 'section form button').click()

        assert selenium.current_url.endswith('/settings/customFields/add/BIKING')
        assert selenium.find_element(By.CLASS_NAME, 'alert-danger') is not None

    def test_add_custom_track_field_name_already_used(self, server, selenium: WebDriver, app):
        self.__create_custom_field(app, 'my_custom_field')
        self.__open_add_form(selenium)

        selenium.find_element(By.ID, 'field-name').send_keys('my_custom_field')
        selenium.find_element(By.CSS_SELECTOR, 'section form button').click()

        assert selenium.current_url.endswith('/settings/customFields/add/BIKING')
        assert selenium.find_element(By.CLASS_NAME, 'alert-danger') is not None

    def test_edit_custom_track_field_valid(self, server, selenium: WebDriver, app):
        self.__create_custom_field(app, 'my_custom_field')
        self.__open_edit_form(selenium)

        selenium.find_element(By.ID, 'participant-name').clear()
        selenium.find_element(By.ID, 'field-name').send_keys('abc')
        selenium.find_element(By.ID, 'field-is-required').click()
        selenium.find_element(By.CSS_SELECTOR, 'section form button').click()

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.TAG_NAME, 'h1'), 'Settings')
        )

        assert len(selenium.find_elements(By.XPATH, '//td[text()="True"]')) == 1

    def test_edit_custom_track_field_reserved_name(self, server, selenium: WebDriver, app):
        self.__create_custom_field(app, 'my_custom_field')
        self.__open_edit_form(selenium)

        selenium.find_element(By.ID, 'field-name').clear()
        selenium.find_element(By.ID, 'field-name').send_keys(RESERVED_FIELD_NAMES[0])
        selenium.find_element(By.CSS_SELECTOR, 'section form button').click()

        assert selenium.current_url.endswith('/settings/customFields/edit/1')
        assert selenium.find_element(By.CLASS_NAME, 'alert-danger') is not None

    def test_edit_custom_track_field_name_already_used(self, server, selenium: WebDriver, app):
        self.__create_custom_field(app, 'my_custom_field')
        self.__create_custom_field(app, 'abc')
        self.__open_edit_form(selenium)

        selenium.find_element(By.ID, 'field-name').clear()
        selenium.find_element(By.ID, 'field-name').send_keys('abc')
        selenium.find_element(By.CSS_SELECTOR, 'section form button').click()

        assert selenium.current_url.endswith('/settings/customFields/edit/1')
        assert selenium.find_element(By.CLASS_NAME, 'alert-danger') is not None
