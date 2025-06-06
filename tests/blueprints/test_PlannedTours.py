import time

import pytest
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait

from sporttracker.logic.model.WorkoutType import WorkoutType
from sporttracker.logic.model.User import create_user, Language
from tests.SeleniumTestBaseClass import SeleniumTestBaseClass
from tests.TestConstants import TEST_USERNAME, TEST_PASSWORD

TEST_USERNAME_2 = 'test_user_2'
TEST_PASSWORD_2 = 'abcdef'


@pytest.fixture(autouse=True)
def prepare_test_data(app):
    with app.app_context():
        create_user(TEST_USERNAME, TEST_PASSWORD, False, Language.ENGLISH)
        create_user(TEST_USERNAME_2, TEST_PASSWORD_2, False, Language.ENGLISH)


class TestPlannedTours(SeleniumTestBaseClass):
    def __open_form(self, selenium):
        selenium.get(self.build_url('/plannedTours'))

        selenium.find_element(By.CLASS_NAME, 'headline').find_element(By.TAG_NAME, 'a').click()
        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'New Planned Tour')
        )

    def __open_edit_form(self, selenium):
        selenium.get(self.build_url('/plannedTours/edit/1'))

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Edit Planned Tour')
        )

    @staticmethod
    def fill_form(
        selenium,
        workoutType,
        name,
        arrivalMethod: str | None,
        departureMethod: str | None,
        direction: str | None,
    ):
        select = Select(selenium.find_element(By.ID, 'planned-tour-type'))
        select.select_by_visible_text(workoutType.name.capitalize())

        nameInput = selenium.find_element(By.ID, 'planned-tour-name')
        nameInput.clear()
        nameInput.send_keys(name)

        if arrivalMethod is not None:
            selenium.find_element(By.XPATH, f'//label[@for="{arrivalMethod}"]').click()

        if departureMethod is not None:
            selenium.find_element(By.XPATH, f'//label[@for="{departureMethod}"]').click()

        if direction is not None:
            selenium.find_element(By.XPATH, f'//label[@for="{direction}"]').click()

    def test_add_tour_valid(self, server, selenium: WebDriver):
        self.login(selenium)
        self.__open_form(selenium)
        self.fill_form(
            selenium,
            WorkoutType.BIKING,
            'Awesome Tour',
            'arrival-method-2',
            'departure-method-2',
            'direction-2',
        )
        self.click_button_by_id(selenium, 'buttonSavePlannedTour')

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Planned Tours')
        )

        assert len(selenium.find_elements(By.CSS_SELECTOR, 'section .card')) == 1

    def test_add_tour_all_empty(self, server, selenium: WebDriver):
        self.login(selenium)
        self.__open_form(selenium)
        self.fill_form(selenium, WorkoutType.BIKING, '', None, None, None)
        self.click_button_by_id(selenium, 'buttonSavePlannedTour')

        assert selenium.current_url.endswith('/plannedTours/add')

    def test_quick_filter_only_show_activated_workout_types(self, server, selenium: WebDriver):
        self.login(selenium)
        self.__open_form(selenium)
        self.fill_form(selenium, WorkoutType.BIKING, 'Awesome Tour', None, None, None)
        self.click_button_by_id(selenium, 'buttonSavePlannedTour')

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Planned Tours')
        )

        self.__open_form(selenium)
        self.fill_form(selenium, WorkoutType.RUNNING, 'Run away', None, None, None)
        self.click_button_by_id(selenium, 'buttonSavePlannedTour')

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Planned Tours')
        )

        selenium.find_elements(By.CLASS_NAME, 'quick-filter')[0].click()

        WebDriverWait(selenium, 5).until(
            expected_conditions.invisibility_of_element_located((By.XPATH, '//h4[text()="New Planned Tour"]'))
        )

        assert len(selenium.find_elements(By.CSS_SELECTOR, 'section .card')) == 1

    def test_filter(self, server, selenium: WebDriver):
        self.login(selenium)
        self.__open_form(selenium)
        self.fill_form(selenium, WorkoutType.BIKING, 'Awesome Tour', 'arrival-method-2', None, None)
        self.click_button_by_id(selenium, 'buttonSavePlannedTour')

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Planned Tours')
        )

        self.__open_form(selenium)
        self.fill_form(selenium, WorkoutType.RUNNING, 'Run away', 'arrival-method-3', None, None)
        self.click_button_by_id(selenium, 'buttonSavePlannedTour')

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Planned Tours')
        )

        buttonFilterArrivalMethod = selenium.find_elements(By.CSS_SELECTOR, '.dropdown.position-static')[3]
        buttonFilterArrivalMethod.click()

        WebDriverWait(buttonFilterArrivalMethod, 5).until(
            expected_conditions.visibility_of_element_located((By.ID, 'plannedTourFilterArrivalMethod-2'))
        )

        buttonFilterArrivalMethod.find_element(By.ID, 'plannedTourFilterArrivalMethod-2').click()
        selenium.find_element(By.ID, 'buttonApplyFilter').click()

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Planned Tours')
        )

        assert len(selenium.find_elements(By.CSS_SELECTOR, 'section .card')) == 1

    def test_edit_tour_valid(self, server, selenium: WebDriver, app):
        self.login(selenium)
        self.__open_form(selenium)
        self.fill_form(
            selenium,
            WorkoutType.BIKING,
            'Awesome Tour',
            'arrival-method-2',
            'departure-method-2',
            'direction-2',
        )
        self.click_button_by_id(selenium, 'buttonSavePlannedTour')

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Planned Tours')
        )

        self.__open_edit_form(selenium)

        assert selenium.find_element(By.ID, 'planned-tour-name').get_attribute('value') == 'Awesome Tour'

        assert selenium.find_element(By.ID, 'arrival-method-2').is_selected()
        assert selenium.find_element(By.ID, 'departure-method-2').is_selected()
        assert selenium.find_element(By.ID, 'direction-2').is_selected()

        self.fill_form(
            selenium,
            WorkoutType.BIKING,
            'Better Tour',
            'arrival-method-3',
            'departure-method-3',
            'direction-3',
        )
        self.click_button_by_id(selenium, 'buttonSavePlannedTour')

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Planned Tours')
        )

        assert len(selenium.find_elements(By.CLASS_NAME, 'planned-tour-name')) == 1

    def test_new_tour_share_with_user(self, server, selenium: WebDriver):
        self.login(selenium)
        self.__open_form(selenium)

        self.fill_form(selenium, WorkoutType.BIKING, 'Awesome Tour', None, None, None)

        selenium.find_element(By.XPATH, '//label[@for="sharedUser-3"]').click()

        self.click_button_by_id(selenium, 'buttonSavePlannedTour')

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Planned Tours')
        )

        cards = selenium.find_elements(By.CSS_SELECTOR, 'section .card')
        assert len(cards) == 1
        # check share icon is displayed
        assert cards[0].find_element(By.XPATH, '//div[contains(text(), "shared")]')

        # check other user can see planned tour
        self.logout(selenium)
        self.login(selenium, username=TEST_USERNAME_2, password=TEST_PASSWORD_2)
        selenium.get(self.build_url('/plannedTours'))
        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Planned Tours')
        )
        cards = selenium.find_elements(By.CSS_SELECTOR, 'section .card')
        assert len(cards) == 1
        # check share icon is displayed
        assert cards[0].find_element(By.XPATH, '//div[contains(text(), "shared")]')
        # check notification "new" is shown
        assert cards[0].find_element(By.XPATH, '//span[contains(text(), "new")]')

        # check other user can not delete planned tour
        self.__open_edit_form(selenium)
        with pytest.raises(NoSuchElementException):
            selenium.find_element(By.ID, 'button-delete')

        # check other user can not uncheck owner as shared user
        sharedUsers = selenium.find_elements(By.CLASS_NAME, 'form-check-input')
        assert not sharedUsers[0].is_enabled()
        assert sharedUsers[1].is_enabled()

        # check other user can edit planned tour
        self.fill_form(selenium, WorkoutType.BIKING, 'Mega Tour', None, None, None)
        self.click_button_by_id(selenium, 'buttonSavePlannedTour')

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Planned Tours')
        )

        assert len(selenium.find_elements(By.CLASS_NAME, 'planned-tour-name')) == 1

        # check notification "updated" is shown
        self.logout(selenium)
        self.login(selenium)
        selenium.get(self.build_url('/plannedTours'))
        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Planned Tours')
        )
        cards = selenium.find_elements(By.CSS_SELECTOR, 'section .card')
        assert len(cards) == 1
        assert cards[0].find_element(By.XPATH, '//span[contains(text(), "updated")]')

    def test_new_tour_share_via_link(self, server, selenium: WebDriver):
        self.login(selenium)
        self.__open_form(selenium)

        self.fill_form(selenium, WorkoutType.BIKING, 'Awesome Tour', None, None, None)

        self.click_button_by_id(selenium, 'buttonCreateSharedLink')
        WebDriverWait(selenium, 5).until(expected_conditions.visibility_of_element_located((By.ID, 'sharedLink')))
        sharedLink = selenium.find_element(By.ID, 'sharedLink').text
        self.click_button_by_id(selenium, 'buttonSavePlannedTour')

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Planned Tours')
        )

        cards = selenium.find_elements(By.CSS_SELECTOR, 'section .card')
        assert len(cards) == 1
        # check share icon is displayed
        assert cards[0].find_element(By.XPATH, '//div[contains(text(), "shared")]')

        # check shared link can be viewed without login
        self.logout(selenium)
        selenium.get(sharedLink)
        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'planned-tour-name'), 'Awesome Tour')
        )

    def test_edit_tour_remove_shared_link(self, server, selenium: WebDriver):
        self.login(selenium)
        self.__open_form(selenium)

        self.fill_form(selenium, WorkoutType.BIKING, 'Awesome Tour', None, None, None)

        self.click_button_by_id(selenium, 'buttonCreateSharedLink')
        WebDriverWait(selenium, 5).until(expected_conditions.visibility_of_element_located((By.ID, 'sharedLink')))
        sharedLink = selenium.find_element(By.ID, 'sharedLink').text
        self.click_button_by_id(selenium, 'buttonSavePlannedTour')
        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Planned Tours')
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
        self.click_button_by_id(selenium, 'buttonSavePlannedTour')
        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Planned Tours')
        )

        # check shared link can no longer bew viewed
        self.logout(selenium)
        selenium.get(sharedLink)
        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.ID, 'errorIcon'), 'error')
        )
