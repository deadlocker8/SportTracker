import pytest
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait

from sporttracker.user.UserEntity import create_user, Language
from sporttracker.workout.WorkoutType import WorkoutType
from tests.SeleniumTestBaseClass import SeleniumTestBaseClass
from tests.TestConstants import TEST_USERNAME, TEST_PASSWORD
from tests.plannedTour.test_PlannedTours import TestPlannedTours

TEST_USERNAME_2 = 'test_user_2'
TEST_PASSWORD_2 = 'abcdef'


@pytest.fixture(autouse=True)
def prepare_test_data(app):
    with app.app_context():
        create_user(TEST_USERNAME, TEST_PASSWORD, False, Language.ENGLISH)
        create_user(TEST_USERNAME_2, TEST_PASSWORD_2, False, Language.ENGLISH)


class TestLongDistanceTours(SeleniumTestBaseClass):
    def __open_form(self, selenium):
        selenium.get(self.build_url('/longDistanceTours'))

        selenium.find_element(By.CLASS_NAME, 'headline').find_element(By.TAG_NAME, 'a').click()
        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'New Long-distance Tour'
            )
        )

    def __open_edit_form(self, selenium):
        selenium.get(self.build_url('/longDistanceTours/edit/1'))

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'headline-text'), 'Edit Long-distance Tour'
            )
        )

    def __create_planned_tour(self, selenium, name):
        selenium.get(self.build_url('/plannedTours'))
        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Planned Tours')
        )

        selenium.find_element(By.CLASS_NAME, 'headline').find_element(By.TAG_NAME, 'a').click()
        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'New Planned Tour')
        )

        TestPlannedTours.fill_form(
            selenium, WorkoutType.BIKING, name, 'arrival-method-2', 'departure-method-2', 'direction-2'
        )

        self.click_button_by_id(selenium, 'buttonSavePlannedTour')

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'planned-tour-name'), name)
        )

    @staticmethod
    def __fill_form(selenium, workoutType, name):
        select = Select(selenium.find_element(By.ID, 'long-distance-tour-type'))
        select.select_by_visible_text(workoutType.name.capitalize())

        nameInput = selenium.find_element(By.ID, 'long-distance-tour-name')
        nameInput.clear()
        nameInput.send_keys(name)

    def test_add_tour_valid(self, server, selenium: WebDriver):
        self.login(selenium)

        self.__create_planned_tour(selenium, 'Stage 1')
        self.__create_planned_tour(selenium, 'Stage 2')
        self.__create_planned_tour(selenium, 'Stage 3')

        self.__open_form(selenium)
        self.__fill_form(selenium, WorkoutType.BIKING, 'Awesome Long-distance Tour')

        # add two stages
        selenium.find_elements(By.CLASS_NAME, 'button-long-distance-tour-add-planned-tour')[0].click()
        selenium.find_elements(By.CLASS_NAME, 'button-long-distance-tour-add-planned-tour')[1].click()

        WebDriverWait(selenium, 5).until(
            expected_conditions.visibility_of_element_located(
                (By.CLASS_NAME, 'button-long-distance-tour-unlink-planned-tour')
            )
        )

        # remove first stage
        selenium.find_elements(By.CLASS_NAME, 'button-long-distance-tour-unlink-planned-tour')[0].click()

        WebDriverWait(selenium, 5).until(
            expected_conditions.visibility_of_element_located(
                (By.CSS_SELECTOR, '.button-long-distance-tour-add-planned-tour[data-id="1"]')
            )
        )

        self.click_button_by_id(selenium, 'buttonSaveLongDistanceTour')

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'planned-tour-name'), 'Awesome Long-distance Tour'
            )
        )

        selenium.get(self.build_url('/longDistanceTours'))
        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Long-distance Tours')
        )

        assert len(selenium.find_elements(By.CSS_SELECTOR, 'section .card')) == 1
        assert selenium.find_element(By.CLASS_NAME, 'long-distance-tour-card-number-of-stages').text == '0 / 1'

    def test_add_tour_all_empty(self, server, selenium: WebDriver):
        self.login(selenium)
        self.__open_form(selenium)
        self.__fill_form(selenium, WorkoutType.BIKING, '')
        self.click_button_by_id(selenium, 'buttonSaveLongDistanceTour')

        assert selenium.current_url.endswith('/longDistanceTours/add')

    def test_quick_filter_only_show_activated_workout_types(self, server, selenium: WebDriver):
        self.login(selenium)
        self.__open_form(selenium)
        self.__fill_form(selenium, WorkoutType.BIKING, 'Awesome Long-distance Tour')
        self.click_button_by_id(selenium, 'buttonSaveLongDistanceTour')

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'planned-tour-name'), 'Awesome Long-distance Tour'
            )
        )

        self.__open_form(selenium)
        self.__fill_form(selenium, WorkoutType.RUNNING, 'Run Boy Run')
        self.click_button_by_id(selenium, 'buttonSaveLongDistanceTour')

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'planned-tour-name'), 'Run Boy Run')
        )

        selenium.get(self.build_url('/longDistanceTours'))
        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Long-distance Tours')
        )

        selenium.find_elements(By.CLASS_NAME, 'quick-filter')[0].click()

        WebDriverWait(selenium, 5).until(
            expected_conditions.invisibility_of_element_located((By.XPATH, '//h4[text()="New Long-distance Tour"]'))
        )

        assert len(selenium.find_elements(By.CSS_SELECTOR, 'section .card')) == 1

    def test_edit_tour_valid(self, server, selenium: WebDriver, app):
        self.login(selenium)

        self.__create_planned_tour(selenium, 'Stage 1')
        self.__create_planned_tour(selenium, 'Stage 2')

        self.__open_form(selenium)
        self.__fill_form(selenium, WorkoutType.BIKING, 'Awesome Long-distance Tour')

        # add a stage
        selenium.find_elements(By.CLASS_NAME, 'button-long-distance-tour-add-planned-tour')[0].click()

        WebDriverWait(selenium, 5).until(
            expected_conditions.visibility_of_element_located(
                (By.CLASS_NAME, 'button-long-distance-tour-unlink-planned-tour')
            )
        )

        self.click_button_by_id(selenium, 'buttonSaveLongDistanceTour')

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'planned-tour-name'), 'Awesome Long-distance Tour'
            )
        )

        self.__open_edit_form(selenium)

        assert (
            selenium.find_element(By.ID, 'long-distance-tour-name').get_attribute('value')
            == 'Awesome Long-distance Tour'
        )

        linkedStages = selenium.find_elements(By.CLASS_NAME, 'button-long-distance-tour-unlink-planned-tour')
        assert len(linkedStages) == 1
        assert linkedStages[0].get_attribute('data-id') == '1'

        self.__fill_form(selenium, WorkoutType.BIKING, 'Better Tour')
        self.click_button_by_id(selenium, 'buttonSaveLongDistanceTour')

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'planned-tour-name'), 'Better Tour')
        )

        selenium.get(self.build_url('/longDistanceTours'))
        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Long-distance Tours')
        )

        assert len(selenium.find_elements(By.CLASS_NAME, 'long-distance-tour-name')) == 1

    def test_new_tour_share_with_user(self, server, selenium: WebDriver):
        self.login(selenium)
        self.__open_form(selenium)

        self.__fill_form(selenium, WorkoutType.BIKING, 'Awesome Long-distance Tour')

        selenium.find_element(By.XPATH, '//label[@for="sharedUser-3"]').click()

        self.click_button_by_id(selenium, 'buttonSaveLongDistanceTour')

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'planned-tour-name'), 'Awesome Long-distance Tour'
            )
        )

        selenium.get(self.build_url('/longDistanceTours'))
        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Long-distance Tours')
        )

        cards = selenium.find_elements(By.CSS_SELECTOR, 'section .card')
        assert len(cards) == 1
        # check share icon is displayed
        assert cards[0].find_element(By.XPATH, '//div[contains(text(), "shared")]')

        # check other user can see long-distance tour
        self.logout(selenium)
        self.login(selenium, username=TEST_USERNAME_2, password=TEST_PASSWORD_2)
        selenium.get(self.build_url('/longDistanceTours'))
        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Long-distance Tours')
        )
        cards = selenium.find_elements(By.CSS_SELECTOR, 'section .card')
        assert len(cards) == 1
        # check share icon is displayed
        assert cards[0].find_element(By.XPATH, '//div[contains(text(), "shared")]')

        # check notification is shown
        selenium.get(self.build_url('/notifications'))
        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Notifications')
        )
        notificationTitles = selenium.find_elements(By.CLASS_NAME, 'notification-title')
        assert len(notificationTitles) == 1
        assert notificationTitles[0].text == 'New shared long-distance tour'

        # check other user can not delete long-distance tour
        self.__open_edit_form(selenium)
        with pytest.raises(NoSuchElementException):
            selenium.find_element(By.ID, 'button-delete')

        # check other user can not uncheck owner as shared user
        sharedUsers = selenium.find_elements(By.CLASS_NAME, 'form-check-input')
        assert not sharedUsers[0].is_enabled()
        assert sharedUsers[1].is_enabled()

        # check other user can edit long-distance tour
        self.__fill_form(selenium, WorkoutType.BIKING, 'Mega Tour')
        self.click_button_by_id(selenium, 'buttonSaveLongDistanceTour')

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'planned-tour-name'), 'Mega Tour')
        )

        selenium.get(self.build_url('/longDistanceTours'))
        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Long-distance Tours')
        )

        assert len(selenium.find_elements(By.CLASS_NAME, 'long-distance-tour-name')) == 1

        # check notification "updated" is shown
        self.logout(selenium)
        self.login(selenium)
        selenium.get(self.build_url('/notifications'))
        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Notifications')
        )
        notificationTitles = selenium.find_elements(By.CLASS_NAME, 'notification-title')
        assert len(notificationTitles) == 1
        assert notificationTitles[0].text == 'Updated shared long-distance tour'
