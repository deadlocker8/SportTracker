import time
from datetime import datetime

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from sporttracker.db import db
from sporttracker.gpx.GpxMetadataEntity import GpxMetadata
from sporttracker.tileHunting.GpxVisitedTileEntity import GpxVisitedTile
from sporttracker.user.UserEntity import create_user, Language
from sporttracker.workout.WorkoutType import WorkoutType
from sporttracker.workout.distance.DistanceWorkoutEntity import DistanceWorkout
from tests.SeleniumTestBaseClass import SeleniumTestBaseClass
from tests.TestConstants import TEST_USERNAME, TEST_PASSWORD


@pytest.fixture(autouse=True)
def prepare_test_data(app):
    with app.app_context():
        user = create_user(TEST_USERNAME, TEST_PASSWORD, False, Language.ENGLISH, 2026)

        __create_workout_with_visited_tile(user.id, 'Biking 2025', datetime(2025, 6, 15, 10, 0), 35198, 21494)
        __create_workout_with_visited_tile(user.id, 'Biking 2026', datetime(2026, 1, 15, 10, 0), 35199, 21495)


def __create_workout_with_visited_tile(userId: int, name: str, startTime: datetime, tileX: int, tileY: int) -> None:
    gpxMetadata = GpxMetadata(
        gpx_file_name='test',
        length=0,
        elevation_minimum=None,
        elevation_maximum=None,
        uphill=None,
        downhill=None,
        editor_link=None,
    )
    db.session.add(gpxMetadata)
    db.session.commit()

    workout = DistanceWorkout(
        type=WorkoutType.BIKING,
        name=name,
        start_time=startTime,
        duration=3600,
        distance=10000,
        user_id=userId,
        custom_fields={},
        share_code=None,
        gpx_metadata_id=gpxMetadata.id,
    )
    db.session.add(workout)
    db.session.commit()

    db.session.add(GpxVisitedTile(workout_id=workout.id, x=tileX, y=tileY))
    db.session.commit()


class TestTileHuntingMap(SeleniumTestBaseClass):
    def __open_filter(self, selenium: WebDriver) -> None:
        filterButton = selenium.find_element(By.CSS_SELECTOR, 'button[data-bs-target="#offcanvas"]')
        selenium.execute_script('arguments[0].scrollIntoView();', filterButton)
        time.sleep(1)
        filterButton.click()
        WebDriverWait(selenium, 5).until(
            expected_conditions.visibility_of_element_located((By.ID, 'quickFilterModeDateRange'))
        )

    def __set_date_range(self, selenium: WebDriver, dateFrom: str, dateTo: str) -> None:
        selenium.find_element(By.XPATH, '//label[@for="quickFilterModeDateRange"]').click()
        dateFromInput = WebDriverWait(selenium, 5).until(
            expected_conditions.visibility_of_element_located((By.ID, 'quickFilterDateFrom'))
        )
        dateToInput = selenium.find_element(By.ID, 'quickFilterDateTo')
        dateFromInput.clear()
        dateFromInput.send_keys(dateFrom)
        dateToInput.clear()
        dateToInput.send_keys(dateTo)
        self.click_button_by_id(selenium, 'buttonApplyFilter')

    @staticmethod
    def __wait_for_tile_count(selenium: WebDriver, expectedCount: int) -> None:
        WebDriverWait(selenium, 10).until(
            expected_conditions.text_to_be_present_in_element((By.TAG_NAME, 'h3'), f'{expectedCount} Tiles visited')
        )

    def __reset_filter(self, selenium: WebDriver) -> None:
        self.__open_filter(selenium)
        resetButton = selenium.find_element(By.ID, 'buttonResetFilter')
        selenium.execute_script('arguments[0].scrollIntoView();', resetButton)
        time.sleep(1)
        resetButton.click()

    def test_date_range_filter(self, server, selenium: WebDriver):
        self.login(selenium)
        selenium.get(self.build_url('/map/tileHunting'))
        self.__wait_for_tile_count(selenium, 2)

        self.__open_filter(selenium)

        # years mode is active by default
        assert selenium.find_element(By.ID, 'quickFilterYearsSection').is_displayed()
        assert not selenium.find_element(By.ID, 'quickFilterDateRangeSection').is_displayed()

        # switching to date range mode shows the date inputs and hides the years section
        selenium.find_element(By.XPATH, '//label[@for="quickFilterModeDateRange"]').click()
        WebDriverWait(selenium, 5).until(
            expected_conditions.visibility_of_element_located((By.ID, 'quickFilterDateFrom'))
        )
        assert not selenium.find_element(By.ID, 'quickFilterYearsSection').is_displayed()
        assert selenium.find_element(By.ID, 'quickFilterDateRangeSection').is_displayed()

        # filter only the 2025 workout
        self.__set_date_range(selenium, '2025-01-01', '2025-12-31')
        self.__wait_for_tile_count(selenium, 1)

        # a range that does not cover any workout hides all tiles
        self.__open_filter(selenium)
        self.__set_date_range(selenium, '2024-01-01', '2024-12-31')
        self.__wait_for_tile_count(selenium, 0)

        # reset shows all tiles again
        self.__reset_filter(selenium)
        self.__wait_for_tile_count(selenium, 2)

    def test_year_filter(self, server, selenium: WebDriver):
        self.login(selenium)
        selenium.get(self.build_url('/map/tileHunting'))
        self.__wait_for_tile_count(selenium, 2)

        self.__open_filter(selenium)

        # all years are checked by default
        assert selenium.find_element(By.ID, 'availableYear-1').is_selected()
        assert selenium.find_element(By.ID, 'availableYear-2').is_selected()

        # unchecking a year hides its tiles
        selenium.find_element(By.XPATH, '//label[normalize-space(text())="2025"]').click()
        self.click_button_by_id(selenium, 'buttonApplyFilter')
        self.__wait_for_tile_count(selenium, 1)

        # unchecking all years hides all tiles
        self.__open_filter(selenium)
        selenium.find_element(By.XPATH, '//label[normalize-space(text())="2026"]').click()
        self.click_button_by_id(selenium, 'buttonApplyFilter')
        self.__wait_for_tile_count(selenium, 0)

        # reset shows all tiles again
        self.__reset_filter(selenium)
        self.__wait_for_tile_count(selenium, 2)

    def test_switch_back_to_years_filter_after_date_range(self, server, selenium: WebDriver):
        self.login(selenium)
        selenium.get(self.build_url('/map/tileHunting'))
        self.__wait_for_tile_count(selenium, 2)

        # apply a date range filter first
        self.__open_filter(selenium)
        self.__set_date_range(selenium, '2025-01-01', '2025-12-31')
        self.__wait_for_tile_count(selenium, 1)

        # the date range mode stays active when reopening the filter
        self.__open_filter(selenium)
        assert selenium.find_element(By.ID, 'quickFilterModeDateRange').is_selected()
        assert selenium.find_element(By.ID, 'quickFilterDateFrom').get_attribute('value') == '2025-01-01'
        assert selenium.find_element(By.ID, 'quickFilterDateTo').get_attribute('value') == '2025-12-31'

        # switching back to years mode clears the date range filter on apply
        selenium.find_element(By.XPATH, '//label[@for="quickFilterModeYears"]').click()
        assert selenium.find_element(By.ID, 'quickFilterYearsSection').is_displayed()
        assert not selenium.find_element(By.ID, 'quickFilterDateRangeSection').is_displayed()
        self.click_button_by_id(selenium, 'buttonApplyFilter')
        self.__wait_for_tile_count(selenium, 2)
