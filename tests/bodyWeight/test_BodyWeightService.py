from datetime import datetime

import pytest

from sporttracker.bodyWeight.BodyWeightEntity import BodyWeight
from sporttracker.bodyWeight.BodyWeightService import (
    BodyWeightService,
    WeightDifferenceType,
)
from sporttracker.db import db
from sporttracker.user.UserEntity import create_user, Language, User
from tests.TestConstants import TEST_USERNAME, TEST_PASSWORD


@pytest.fixture(autouse=True)
def prepare_test_data(app):
    with app.app_context():
        create_user(TEST_USERNAME, TEST_PASSWORD, False, Language.ENGLISH, 2026)


class TestBodyWeightServiceDelta:
    @staticmethod
    def __get_user_id() -> int:
        user = User.query.filter(User.username == TEST_USERNAME).first()
        if user is None:
            raise ValueError(f'Could not find user with username {TEST_USERNAME}')
        return user.id

    @staticmethod
    def __add_entry(user_id: int, date: datetime, weight: int) -> None:
        db.session.add(BodyWeight(datetime=date, weight=weight, user_id=user_id))
        db.session.commit()

    def test_get_entries_with_difference_no_entries(self, app):
        with app.app_context():
            assert BodyWeightService.get_entries_with_difference(self.__get_user_id()) == []

    def test_get_entries_with_difference_single_entry(self, app):
        with app.app_context():
            self.__add_entry(self.__get_user_id(), datetime(2024, 1, 1, 15, 30), 80000)

            models = BodyWeightService.get_entries_with_difference(self.__get_user_id())
            assert len(models) == 1
            assert models[0].weight == 80000
            assert models[0].difference is None
            assert models[0].difference_formatted == ''
            assert models[0].difference_type == WeightDifferenceType.EQUAL

    def test_get_entries_with_difference_weight_increased(self, app):
        with app.app_context():
            user_id = self.__get_user_id()
            self.__add_entry(user_id, datetime(2024, 1, 1, 15, 30), 80000)
            self.__add_entry(user_id, datetime(2024, 1, 2, 15, 30), 80300)

            models = BodyWeightService.get_entries_with_difference(user_id)
            assert len(models) == 2
            assert models[0].weight == 80300
            assert models[0].difference == 300
            assert models[0].difference_formatted == '+0.3 kg'
            assert models[0].difference_type == WeightDifferenceType.MORE
            assert models[1].weight == 80000
            assert models[1].difference is None
            assert models[1].difference_formatted == ''

    def test_get_entries_with_difference_weight_decreased(self, app):
        with app.app_context():
            user_id = self.__get_user_id()
            self.__add_entry(user_id, datetime(2024, 1, 1, 15, 30), 80300)
            self.__add_entry(user_id, datetime(2024, 1, 2, 15, 30), 80000)

            models = BodyWeightService.get_entries_with_difference(user_id)
            assert len(models) == 2
            assert models[0].weight == 80000
            assert models[0].difference == -300
            assert models[0].difference_formatted == '-0.3 kg'
            assert models[0].difference_type == WeightDifferenceType.LESS

    def test_get_entries_with_difference_weight_unchanged(self, app):
        with app.app_context():
            user_id = self.__get_user_id()
            self.__add_entry(user_id, datetime(2024, 1, 1, 15, 30), 80000)
            self.__add_entry(user_id, datetime(2024, 1, 2, 15, 30), 80000)

            models = BodyWeightService.get_entries_with_difference(user_id)
            assert len(models) == 2
            assert models[0].weight == 80000
            assert models[0].difference == 0
            assert models[0].difference_formatted == '±0.0 kg'
            assert models[0].difference_type == WeightDifferenceType.EQUAL

    def test_get_entries_with_difference_sorted_descending(self, app):
        with app.app_context():
            user_id = self.__get_user_id()
            self.__add_entry(user_id, datetime(2024, 1, 1, 15, 30), 80000)
            self.__add_entry(user_id, datetime(2024, 1, 2, 15, 30), 80300)
            self.__add_entry(user_id, datetime(2024, 1, 3, 15, 30), 80200)

            models = BodyWeightService.get_entries_with_difference(user_id)
            assert [model.entry_datetime for model in models] == [
                datetime(2024, 1, 3, 15, 30),
                datetime(2024, 1, 2, 15, 30),
                datetime(2024, 1, 1, 15, 30),
            ]
            assert [model.difference for model in models] == [-100, 300, None]

    def test_add_and_update_body_weight_entry(self, app):
        with app.app_context():
            user_id = self.__get_user_id()
            BodyWeightService.add_body_weight_entry(
                entry_datetime=datetime(2024, 1, 1, 15, 30), weight=80000, user_id=user_id
            )

            entry = BodyWeight.query.filter(BodyWeight.user_id == user_id).first()
            assert entry is not None

            BodyWeightService.update_body_weight_entry(entry, datetime(2024, 2, 1, 8, 15), 79000)

            updatedEntry = BodyWeight.query.filter(BodyWeight.user_id == user_id).first()
            assert updatedEntry is not None
            assert updatedEntry.weight == 79000
            assert updatedEntry.get_date() == '2024-02-01'
            assert updatedEntry.get_time() == '08:15'

            BodyWeightService.delete_body_weight_entry(updatedEntry)
            assert BodyWeight.query.filter(BodyWeight.user_id == user_id).first() is None


class TestBodyWeightServiceBmi:
    def test_calculate_bmi_no_weight_should_return_none(self):
        assert BodyWeightService.calculate_bmi(None, 180) is None

    def test_calculate_bmi_no_height_should_return_none(self):
        assert BodyWeightService.calculate_bmi(80000, None) is None

    def test_calculate_bmi_zero_height_should_return_none(self):
        assert BodyWeightService.calculate_bmi(80000, 0) is None

    def test_calculate_bmi_valid(self):
        assert BodyWeightService.calculate_bmi(80000, 180) == pytest.approx(24.69, abs=0.01)
