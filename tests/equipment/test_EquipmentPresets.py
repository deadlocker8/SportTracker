from datetime import date

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from sporttracker.db import db
from sporttracker.equipment.bike.BikeEntity import Bike
from sporttracker.equipment.clothes.ClothesEntity import Clothes
from sporttracker.equipment.clothes.ClothesType import ClothesType
from sporttracker.equipment.custom.CustomEquipmentEntity import CustomEquipment
from sporttracker.equipment.EquipmentEntity import Equipment, equipment_preset_equipment_association
from sporttracker.equipment.presets.EquipmentPresetService import EquipmentPresetService
from sporttracker.user.UserEntity import Language, User, create_user
from sporttracker.workout.WorkoutType import WorkoutType
from tests.SeleniumTestBaseClass import SeleniumTestBaseClass
from tests.TestConstants import TEST_PASSWORD, TEST_USERNAME


@pytest.fixture(autouse=True)
def prepare_test_data(app):
    with app.app_context():
        user = create_user(TEST_USERNAME, TEST_PASSWORD, False, Language.ENGLISH, 2026)

        db.session.add(
            Bike(
                name='My Bike',
                workout_type=WorkoutType.BIKING,
                purchase_date=date(2020, 1, 1),
                is_active=True,
                user_id=user.id,
            )
        )
        db.session.add(
            Clothes(
                name='My Clothes',
                workout_type=WorkoutType.BIKING,
                purchase_date=date(2021, 1, 1),
                clothes_type=ClothesType.TOPS,
                is_active=True,
                user_id=user.id,
            )
        )
        db.session.add(
            CustomEquipment(
                name='My Custom Equipment',
                workout_type=WorkoutType.BIKING,
                purchase_date=date(2022, 1, 1),
                is_active=True,
                user_id=user.id,
            )
        )
        db.session.commit()


class TestEquipmentPresets(SeleniumTestBaseClass):
    @staticmethod
    def __get_user_id() -> int:
        user = User.query.filter(User.username == TEST_USERNAME).first()
        if user is None:
            raise ValueError(f'Could not find user with username {TEST_USERNAME}')

        return user.id

    @staticmethod
    def __get_equipment_id(name: str) -> int:
        equipment = Equipment.query.filter(Equipment.name == name).first()
        if equipment is None:
            raise ValueError(f'Could not find equipment with name {name}')

        return equipment.id

    @staticmethod
    def __get_selection_icon(selenium: WebDriver, equipment_id: int):
        return selenium.find_element(
            By.CSS_SELECTOR, f'.equipment-modal-card[data-equipment-id="{equipment_id}"] .equipment-select-icon'
        )

    @staticmethod
    def __toggle_equipment(selenium: WebDriver, equipment_id: int) -> None:
        card = WebDriverWait(selenium, 5).until(
            expected_conditions.visibility_of_element_located(
                (By.CSS_SELECTOR, f'.equipment-modal-card[data-equipment-id="{equipment_id}"]')
            )
        )
        selenium.execute_script('arguments[0].click();', card)

    @staticmethod
    def __wait_for_preset_card(selenium: WebDriver, name: str):
        return WebDriverWait(selenium, 5).until(
            expected_conditions.visibility_of_element_located(
                (
                    By.XPATH,
                    f'//div[contains(@class, "card")][.//div[contains(@class, "fs-5") and normalize-space()="{name}"]]',
                )
            )
        )

    def test_add_and_edit_preset(self, app):
        with app.app_context():
            user_id = self.__get_user_id()
            bike_id = self.__get_equipment_id('My Bike')
            clothes_id = self.__get_equipment_id('My Clothes')

            preset = EquipmentPresetService.add('Weekend', WorkoutType.BIKING, [bike_id, clothes_id], user_id)

            assert preset.name == 'Weekend'
            assert {equipment.id for equipment in preset.equipment} == {bike_id, clothes_id}

            EquipmentPresetService.edit(preset.id, 'Weekday', [bike_id], user_id)

            updatedPreset = EquipmentPresetService.get_by_id(preset.id, user_id)
            assert updatedPreset is not None
            assert updatedPreset.name == 'Weekday'
            assert {equipment.id for equipment in updatedPreset.equipment} == {bike_id}

    def test_delete_preset_keeps_equipment(self, app):
        with app.app_context():
            user_id = self.__get_user_id()
            bike_id = self.__get_equipment_id('My Bike')

            preset = EquipmentPresetService.add('Weekend', WorkoutType.BIKING, [bike_id], user_id)
            preset_id = preset.id

            EquipmentPresetService.delete(preset_id, user_id)

            assert EquipmentPresetService.get_by_id(preset_id, user_id) is None
            assert Equipment.query.filter(Equipment.id == bike_id).first() is not None
            assert Equipment.query.count() == 3

    def test_delete_preset_removes_association_rows(self, app):
        with app.app_context():
            user_id = self.__get_user_id()
            bike_id = self.__get_equipment_id('My Bike')

            preset = EquipmentPresetService.add('Weekend', WorkoutType.BIKING, [bike_id], user_id)
            preset_id = preset.id

            assert db.session.execute(equipment_preset_equipment_association.select()).all() != []

            EquipmentPresetService.delete(preset_id, user_id)

            assert db.session.execute(equipment_preset_equipment_association.select()).all() == []

    def test_add_preset_with_equipment(self, server, selenium: WebDriver, app):
        with app.app_context():
            bike_id = self.__get_equipment_id('My Bike')
            clothes_id = self.__get_equipment_id('My Clothes')

        self.login(selenium)
        selenium.get(self.build_url('/equipment/presets/add/BIKING'))

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'New Equipment Preset')
        )

        selenium.find_element(By.ID, 'equipment-preset-name').send_keys('My Preset')

        self.__toggle_equipment(selenium, bike_id)
        self.__toggle_equipment(selenium, clothes_id)

        assert self.__get_selection_icon(selenium, bike_id).get_attribute('data-selected') == 'true'
        assert self.__get_selection_icon(selenium, clothes_id).get_attribute('data-selected') == 'true'

        self.click_button_by_id(selenium, 'buttonSaveEquipmentPreset')

        card = self.__wait_for_preset_card(selenium, 'My Preset')
        assert '2 selected' in card.text

    def test_edit_preset_with_equipment(self, server, selenium: WebDriver, app):
        with app.app_context():
            user_id = self.__get_user_id()
            bike_id = self.__get_equipment_id('My Bike')
            clothes_id = self.__get_equipment_id('My Clothes')

            preset = EquipmentPresetService.add('Old Preset', WorkoutType.BIKING, [bike_id], user_id)
            preset_id = preset.id

        self.login(selenium)
        selenium.get(self.build_url(f'/equipment/presets/edit/{preset_id}'))

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'Edit Equipment Preset')
        )

        name_input = selenium.find_element(By.ID, 'equipment-preset-name')
        assert name_input.get_attribute('value') == 'Old Preset'
        name_input.clear()
        name_input.send_keys('Updated Preset')

        assert self.__get_selection_icon(selenium, bike_id).get_attribute('data-selected') == 'true'
        assert self.__get_selection_icon(selenium, clothes_id).get_attribute('data-selected') == 'false'

        self.__toggle_equipment(selenium, bike_id)
        self.__toggle_equipment(selenium, clothes_id)

        assert self.__get_selection_icon(selenium, bike_id).get_attribute('data-selected') == 'false'
        assert self.__get_selection_icon(selenium, clothes_id).get_attribute('data-selected') == 'true'

        self.click_button_by_id(selenium, 'buttonSaveEquipmentPreset')

        card = self.__wait_for_preset_card(selenium, 'Updated Preset')
        assert '1 selected' in card.text

    def test_add_preset_without_equipment(self, server, selenium: WebDriver, app):
        self.login(selenium)
        selenium.get(self.build_url('/equipment/presets/add/BIKING'))

        WebDriverWait(selenium, 5).until(
            expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, 'headline-text'), 'New Equipment Preset')
        )

        selenium.find_element(By.ID, 'equipment-preset-name').send_keys('Empty Preset')
        self.click_button_by_id(selenium, 'buttonSaveEquipmentPreset')

        card = self.__wait_for_preset_card(selenium, 'Empty Preset')
        assert '0 selected' in card.text
