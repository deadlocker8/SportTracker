import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from tests.SeleniumTestBaseClass import SeleniumTestBaseClass
from tests.TestConstants import TEST_USERNAME, TEST_PASSWORD
from sporttracker.user.UserEntity import create_user, Language


@pytest.fixture(autouse=True)
def prepare_test_data(app):
    with app.app_context():
        create_user(TEST_USERNAME, TEST_PASSWORD, False, Language.ENGLISH)


class TestMonthGoals(SeleniumTestBaseClass):
    def test_month_goals_no_goals(self, server, selenium: WebDriver):
        self.login(selenium)
        selenium.get(self.build_url('/goals'))
        assert 'Month Goals' in selenium.find_element(By.CLASS_NAME, 'headline-text').text


class TestMonthGoalsDistance(SeleniumTestBaseClass):
    def __open_form(self, selenium, index, expectedTitle):
        self.login(selenium)
        selenium.get(self.build_url('/goals'))

        # open goal chooser
        selenium.find_element(By.CLASS_NAME, 'headline').find_element(By.TAG_NAME, 'a').click()
        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'New Month Goal')
        )

        # click button to create new goal
        buttons = selenium.find_elements(By.CSS_SELECTOR, 'section .btn')
        buttons[index].click()
        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), expectedTitle)
        )

    @staticmethod
    def __fill_and_submit_form(selenium, year, month, minimum, perfect):
        selenium.find_element(By.ID, 'month-goal-year').send_keys(year)
        selenium.find_element(By.ID, 'month-goal-month').send_keys(month)
        selenium.find_element(By.ID, 'month-goal-minimum').send_keys(minimum)
        selenium.find_element(By.ID, 'month-goal-perfect').send_keys(perfect)
        selenium.find_element(By.CSS_SELECTOR, 'section form button').click()

    @staticmethod
    def __fill_and_submit_multiple_form(selenium, starYear, startMonth, endYear, endMonth, minimum, perfect):
        selenium.find_element(By.ID, 'month-goal-start-year').send_keys(starYear)
        selenium.find_element(By.ID, 'month-goal-start-month').send_keys(startMonth)
        selenium.find_element(By.ID, 'month-goal-end-year').send_keys(endYear)
        selenium.find_element(By.ID, 'month-goal-end-month').send_keys(endMonth)
        selenium.find_element(By.ID, 'month-goal-minimum').send_keys(minimum)
        selenium.find_element(By.ID, 'month-goal-perfect').send_keys(perfect)
        selenium.find_element(By.CSS_SELECTOR, 'section form button').click()

    def test_add_distance_goal_valid(self, server, selenium: WebDriver):
        self.__open_form(selenium, 0, 'New Distance Month Goal')
        self.__fill_and_submit_form(selenium, 2024, 2, 100, 200)

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Month Goals')
        )

        assert len(selenium.find_elements(By.CSS_SELECTOR, 'section .d-lg-block .progress')) == 1

    def test_add_distance_goal_all_empty(self, server, selenium: WebDriver):
        self.__open_form(selenium, 0, 'New Distance Month Goal')
        self.__fill_and_submit_form(selenium, '', '', '', '')
        assert selenium.current_url.endswith('/goalsDistance/add')

    def test_add_multiple_distance_goals_valid(self, server, selenium: WebDriver):
        self.__open_form(selenium, 1, 'Multiple New Distance Month Goals')
        self.__fill_and_submit_multiple_form(selenium, 2023, 11, 2024, 2, 100, 200)

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Month Goals')
        )

        assert len(selenium.find_elements(By.CSS_SELECTOR, 'section .d-lg-block .progress')) == 4

    def test_add_multiple_distance_goals_all_empty(self, server, selenium: WebDriver):
        self.__open_form(selenium, 1, 'Multiple New Distance Month Goals')
        self.__fill_and_submit_multiple_form(selenium, '', '', '', '', '', '')
        assert selenium.current_url.endswith('/goalsDistance/addMultiple')


class TestMonthGoalsCount(SeleniumTestBaseClass):
    def __open_form(self, selenium, index, expectedTitle):
        self.login(selenium)
        selenium.get(self.build_url('/goals'))

        # open goal chooser
        selenium.find_element(By.CLASS_NAME, 'headline').find_element(By.TAG_NAME, 'a').click()
        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'New Month Goal')
        )

        # click button to create new goal
        buttons = selenium.find_elements(By.CSS_SELECTOR, 'section .btn')
        buttons[index].click()
        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), expectedTitle)
        )

    @staticmethod
    def __fill_and_submit_form(selenium, year, month, minimum, perfect):
        selenium.find_element(By.ID, 'month-goal-year').send_keys(year)
        selenium.find_element(By.ID, 'month-goal-month').send_keys(month)
        selenium.find_element(By.ID, 'month-goal-minimum').send_keys(minimum)
        selenium.find_element(By.ID, 'month-goal-perfect').send_keys(perfect)
        selenium.find_element(By.CSS_SELECTOR, 'section form button').click()

    @staticmethod
    def __fill_and_submit_multiple_form(selenium, starYear, startMonth, endYear, endMonth, minimum, perfect):
        selenium.find_element(By.ID, 'month-goal-start-year').send_keys(starYear)
        selenium.find_element(By.ID, 'month-goal-start-month').send_keys(startMonth)
        selenium.find_element(By.ID, 'month-goal-end-year').send_keys(endYear)
        selenium.find_element(By.ID, 'month-goal-end-month').send_keys(endMonth)
        selenium.find_element(By.ID, 'month-goal-minimum').send_keys(minimum)
        selenium.find_element(By.ID, 'month-goal-perfect').send_keys(perfect)
        selenium.find_element(By.CSS_SELECTOR, 'section form button').click()

    def test_add_count_goal_valid(self, server, selenium: WebDriver):
        self.__open_form(selenium, 2, 'New Count Month Goal')
        self.__fill_and_submit_form(selenium, 2024, 2, 100, 200)

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Month Goals')
        )

        assert len(selenium.find_elements(By.CSS_SELECTOR, 'section .d-lg-block .progress')) == 1

    def test_add_count_goal_all_empty(self, server, selenium: WebDriver):
        self.__open_form(selenium, 2, 'New Count Month Goal')
        self.__fill_and_submit_form(selenium, '', '', '', '')
        assert selenium.current_url.endswith('/goalsCount/add')

    def test_add_count_distance_goals_valid(self, server, selenium: WebDriver):
        self.__open_form(selenium, 3, 'Multiple New Count Month Goals')
        self.__fill_and_submit_multiple_form(selenium, 2023, 11, 2024, 2, 100, 200)

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Month Goals')
        )

        assert len(selenium.find_elements(By.CSS_SELECTOR, 'section .d-lg-block .progress')) == 4

    def test_add_multiple_count_goals_all_empty(self, server, selenium: WebDriver):
        self.__open_form(selenium, 3, 'Multiple New Count Month Goals')
        self.__fill_and_submit_multiple_form(selenium, '', '', '', '', '', '')
        assert selenium.current_url.endswith('/goalsCount/addMultiple')


class TestMonthGoalsDuration(SeleniumTestBaseClass):
    def __open_form(self, selenium, index, expectedTitle):
        self.login(selenium)
        selenium.get(self.build_url('/goals'))

        # open goal chooser
        selenium.find_element(By.CLASS_NAME, 'headline').find_element(By.TAG_NAME, 'a').click()
        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'New Month Goal')
        )

        # click button to create new goal
        buttons = selenium.find_elements(By.CSS_SELECTOR, 'section .btn')
        buttons[index].click()
        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), expectedTitle)
        )

    @staticmethod
    def __fill_and_submit_form(selenium, year, month, minimumHours, minimumMinutes, perfectHours, perfectMinutes):
        selenium.find_element(By.ID, 'month-goal-year').send_keys(year)
        selenium.find_element(By.ID, 'month-goal-month').send_keys(month)
        selenium.find_element(By.ID, 'month-goal-minimum-hours').send_keys(minimumHours)
        selenium.find_element(By.ID, 'month-goal-minimum-minutes').send_keys(minimumMinutes)
        selenium.find_element(By.ID, 'month-goal-perfect-hours').send_keys(perfectHours)
        selenium.find_element(By.ID, 'month-goal-perfect-minutes').send_keys(perfectMinutes)
        selenium.find_element(By.CSS_SELECTOR, 'section form button').click()

    @staticmethod
    def __fill_and_submit_multiple_form(
        selenium,
        starYear,
        startMonth,
        endYear,
        endMonth,
        minimumHours,
        minimumMinutes,
        perfectHours,
        perfectMinutes,
    ):
        selenium.find_element(By.ID, 'month-goal-start-year').send_keys(starYear)
        selenium.find_element(By.ID, 'month-goal-start-month').send_keys(startMonth)
        selenium.find_element(By.ID, 'month-goal-end-year').send_keys(endYear)
        selenium.find_element(By.ID, 'month-goal-end-month').send_keys(endMonth)
        selenium.find_element(By.ID, 'month-goal-minimum-hours').send_keys(minimumHours)
        selenium.find_element(By.ID, 'month-goal-minimum-minutes').send_keys(minimumMinutes)
        selenium.find_element(By.ID, 'month-goal-perfect-hours').send_keys(perfectHours)
        selenium.find_element(By.ID, 'month-goal-perfect-minutes').send_keys(perfectMinutes)
        selenium.find_element(By.CSS_SELECTOR, 'section form button').click()

    def test_add_duration_goal_valid(self, server, selenium: WebDriver):
        self.__open_form(selenium, 4, 'New Duration Month Goal')
        self.__fill_and_submit_form(selenium, 2024, 2, 1, 30, 3, 0)

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Month Goals')
        )

        assert len(selenium.find_elements(By.CSS_SELECTOR, 'section .d-lg-block .progress')) == 1

    def test_add_duration_goal_all_empty(self, server, selenium: WebDriver):
        self.__open_form(selenium, 4, 'New Duration Month Goal')
        self.__fill_and_submit_form(selenium, '', '', '', '', '', '')
        assert selenium.current_url.endswith('/goalsDuration/add')

    def test_add_multiple_duration_goals_valid(self, server, selenium: WebDriver):
        self.__open_form(selenium, 5, 'Multiple New Duration Month Goals')
        self.__fill_and_submit_multiple_form(selenium, 2023, 11, 2024, 2, 1, 30, 3, 0)

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Month Goals')
        )

        assert len(selenium.find_elements(By.CSS_SELECTOR, 'section .d-lg-block .progress')) == 4

    def test_add_multiple_duration_goals_all_empty(self, server, selenium: WebDriver):
        self.__open_form(selenium, 5, 'Multiple New Duration Month Goals')
        self.__fill_and_submit_multiple_form(selenium, '', '', '', '', '', '', '', '')
        assert selenium.current_url.endswith('/goalsDuration/addMultiple')
