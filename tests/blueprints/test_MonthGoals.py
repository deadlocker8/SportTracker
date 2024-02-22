import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from tests.SeleniumTestBaseClass import SeleniumTestBaseClass
from tests.TestConstants import TEST_USERNAME, TEST_PASSWORD
from sporttracker.logic.model.User import create_user, Language


@pytest.fixture(autouse=True)
def prepare_test_data(app):
    with app.app_context():
        create_user(TEST_USERNAME, TEST_PASSWORD, False, Language.ENGLISH)


class TestMonthGoals(SeleniumTestBaseClass):
    def test_month_goals_no_goals(self, server, selenium: WebDriver):
        self.login(selenium)
        selenium.get(self.build_url('/goals'))
        assert 'Month Goals' in selenium.find_element(By.TAG_NAME, 'h1').text


class TestMonthGoalsDistance(SeleniumTestBaseClass):
    def __open_form(self, selenium):
        self.login(selenium)
        selenium.get(self.build_url('/goals'))

        # open goal chooser
        selenium.find_element(By.TAG_NAME, 'h1').find_element(By.TAG_NAME, 'a').click()
        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.TAG_NAME, 'h1'), 'New Month Goal')
        )

        # click button to create new distance goal
        buttons = selenium.find_elements(By.CSS_SELECTOR, 'section .btn')
        buttons[0].click()
        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element(
                (By.TAG_NAME, 'h1'), 'New Distance Month Goal'
            )
        )

    @staticmethod
    def __fill_and_submit_form(selenium, year, month, minimum, perfect):
        selenium.find_element(By.ID, 'month-goal-year').send_keys(year)
        selenium.find_element(By.ID, 'month-goal-month').send_keys(month)
        selenium.find_element(By.ID, 'month-goal-minimum').send_keys(minimum)
        selenium.find_element(By.ID, 'month-goal-perfect').send_keys(perfect)
        selenium.find_element(By.CSS_SELECTOR, 'section form button').click()

    def test_add_distance_goal_valid(self, server, selenium: WebDriver):
        self.__open_form(selenium)
        self.__fill_and_submit_form(selenium, 2024, 2, 100, 200)

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.TAG_NAME, 'h1'), 'Month Goals')
        )

        assert len(selenium.find_elements(By.CSS_SELECTOR, 'section .progress')) == 1

    def test_add_distance_goal_all_empty(self, server, selenium: WebDriver):
        self.__open_form(selenium)
        self.__fill_and_submit_form(selenium, '', '', '', '')
        assert selenium.current_url.endswith('/goalsDistance/add')

    def test_add_distance_goal_year_empty(self, server, selenium: WebDriver):
        self.__open_form(selenium)
        self.__fill_and_submit_form(selenium, '', 2, 100, 200)
        assert selenium.current_url.endswith('/goalsDistance/add')

    def test_add_distance_goal_month_empty(self, server, selenium: WebDriver):
        self.__open_form(selenium)
        self.__fill_and_submit_form(selenium, 2024, '', 100, 200)
        assert selenium.current_url.endswith('/goalsDistance/add')

    def test_add_distance_goal_minimum_empty(self, server, selenium: WebDriver):
        self.__open_form(selenium)
        self.__fill_and_submit_form(selenium, 2024, 2, '', 200)
        assert selenium.current_url.endswith('/goalsDistance/add')

    def test_add_distance_goal_perfect_empty(self, server, selenium: WebDriver):
        self.__open_form(selenium)
        self.__fill_and_submit_form(selenium, 2024, 2, 100, '')
        assert selenium.current_url.endswith('/goalsDistance/add')
