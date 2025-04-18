import time
from abc import ABC
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from tests.TestConstants import TEST_PORT, TEST_USERNAME, TEST_PASSWORD


class SeleniumTestBaseClass(ABC):
    @staticmethod
    def get_base_url() -> str:
        return f'http://127.0.0.1:{TEST_PORT}'

    @staticmethod
    def build_url(path: str):
        return f'{SeleniumTestBaseClass.get_base_url()}{path}'

    @staticmethod
    def login(selenium, username=TEST_USERNAME, password=TEST_PASSWORD) -> None:
        selenium.get(SeleniumTestBaseClass.get_base_url())

        selenium.find_element(By.ID, 'username').send_keys(username)
        selenium.find_element(By.ID, 'password').send_keys(password)
        selenium.find_elements(By.TAG_NAME, 'button')[0].click()

        now = datetime.now()
        assert selenium.current_url.endswith(f'/workouts/{now.year}/{now.month}')

    @staticmethod
    def logout(selenium) -> None:
        selenium.find_element(By.CLASS_NAME, 'user-name-max-width').click()
        WebDriverWait(selenium, 5).until(expected_conditions.visibility_of_element_located((By.ID, 'button-logout')))
        selenium.find_element(By.ID, 'button-logout').click()

    @staticmethod
    def click_button_by_id(selenium, buttonId: str) -> None:
        button = selenium.find_element(By.ID, buttonId)
        selenium.execute_script('arguments[0].scrollIntoView();', button)
        time.sleep(1)
        button.click()
