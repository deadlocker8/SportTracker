import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver

from SeleniumTestBaseClass import SeleniumTestBaseClass
from TestConstants import TEST_USERNAME, TEST_PASSWORD
from sporttracker.logic.model.User import create_user, Language


@pytest.fixture(scope='session', autouse=True)
def prepare_test_data(app):
    with app.app_context():
        create_user(TEST_USERNAME, TEST_PASSWORD, False, Language.ENGLISH)


class TestMonthGoals(SeleniumTestBaseClass):
    def test_month_goals_no_goals(self, server, selenium: WebDriver):
        self.login(selenium)
        selenium.get(self.build_url('/goals'))
        assert 'Month Goals' in selenium.find_element(By.TAG_NAME, 'h1').text
