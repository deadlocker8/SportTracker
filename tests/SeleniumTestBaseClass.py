from abc import ABC
from datetime import datetime

from selenium.webdriver.common.by import By

from tests.TestConstants import TEST_PORT, TEST_USERNAME, TEST_PASSWORD


class SeleniumTestBaseClass(ABC):
    @staticmethod
    def get_base_url() -> str:
        return f'http://127.0.0.1:{TEST_PORT}'

    @staticmethod
    def build_url(path: str):
        return f'{SeleniumTestBaseClass.get_base_url()}{path}'

    @staticmethod
    def login(selenium) -> None:
        selenium.get(SeleniumTestBaseClass.get_base_url())

        selenium.find_element(By.ID, 'username').send_keys(TEST_USERNAME)
        selenium.find_element(By.ID, 'password').send_keys(TEST_PASSWORD)
        selenium.find_elements(By.TAG_NAME, 'button')[1].click()

        now = datetime.now()
        assert selenium.current_url.endswith(f'/tracks/{now.year}/{now.month}')
