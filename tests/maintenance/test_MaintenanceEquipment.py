from datetime import date, datetime

import pytest

from sporttracker.db import db
from sporttracker.equipment.bike.BikeEntity import Bike
from sporttracker.equipment.clothes.ClothesEntity import Clothes
from sporttracker.equipment.clothes.ClothesType import ClothesType
from sporttracker.equipment.custom.CustomEquipmentEntity import CustomEquipment
from sporttracker.equipment.EquipmentService import EquipmentService
from sporttracker.equipment.EquipmentType import EquipmentType
from sporttracker.user.UserEntity import Language, User, create_user
from sporttracker.workout.distance.DistanceWorkoutEntity import DistanceWorkout
from sporttracker.workout.distance.DistanceWorkoutService import DistanceWorkoutService
from sporttracker.workout.WorkoutType import WorkoutType
from tests.TestConstants import TEST_PASSWORD, TEST_USERNAME


@pytest.fixture(autouse=True)
def prepare_test_data(app):
    with app.app_context():
        user = create_user(TEST_USERNAME, TEST_PASSWORD, False, Language.ENGLISH, 2026)

        db.session.add_all(
            [
                Bike(
                    name='Bike 1',
                    workout_type=WorkoutType.BIKING,
                    is_owned=True,
                    purchase_date=date(2020, 1, 1),
                    is_active=True,
                    user_id=user.id,
                ),
                Bike(
                    name='Bike 2',
                    workout_type=WorkoutType.BIKING,
                    is_owned=True,
                    purchase_date=date(2021, 1, 1),
                    is_active=True,
                    user_id=user.id,
                ),
                Clothes(
                    name='Clothes 1',
                    workout_type=WorkoutType.BIKING,
                    is_owned=True,
                    purchase_date=date(2021, 1, 1),
                    clothes_type=ClothesType.TOPS,
                    is_active=True,
                    user_id=user.id,
                ),
                CustomEquipment(
                    name='Inactive Equipment',
                    workout_type=WorkoutType.BIKING,
                    is_owned=True,
                    purchase_date=date(2022, 1, 1),
                    is_active=False,
                    user_id=user.id,
                ),
            ]
        )
        db.session.commit()


class TestMaintenanceEquipment:
    @staticmethod
    def __get_user() -> User:
        user = User.query.filter(User.username == TEST_USERNAME).first()
        if user is None:
            raise ValueError(f'Could not find user with username {TEST_USERNAME}')
        return user

    def test_get_equipment_grouped_by_workout_type_and_type_only_returns_active_equipment(self, app):
        with app.app_context():
            user = self.__get_user()

            groupedEquipment = EquipmentService.get_equipment_grouped_by_workout_type_and_type(
                [WorkoutType.BIKING], user.id
            )

            assert [equipment.name for equipment in groupedEquipment[WorkoutType.BIKING][EquipmentType.BIKE]] == [
                'Bike 1',
                'Bike 2',
            ]
            assert [equipment.name for equipment in groupedEquipment[WorkoutType.BIKING][EquipmentType.CLOTHES]] == [
                'Clothes 1'
            ]
            assert EquipmentType.CUSTOM not in groupedEquipment[WorkoutType.BIKING]

    def test_get_equipment_grouped_by_workout_type_and_type_includes_selected_inactive_equipment(self, app):
        with app.app_context():
            user = self.__get_user()
            inactiveEquipment = CustomEquipment.query.filter(CustomEquipment.name == 'Inactive Equipment').first()
            assert inactiveEquipment is not None

            groupedEquipment = EquipmentService.get_equipment_grouped_by_workout_type_and_type(
                [WorkoutType.BIKING], user.id, inactiveEquipment.id
            )

            assert [equipment.name for equipment in groupedEquipment[WorkoutType.BIKING][EquipmentType.CUSTOM]] == [
                'Inactive Equipment'
            ]

    def test_get_distance_between_dates_filters_by_equipment(self, app):
        with app.app_context():
            user = self.__get_user()
            bike1 = Bike.query.filter(Bike.name == 'Bike 1').first()
            bike2 = Bike.query.filter(Bike.name == 'Bike 2').first()
            assert bike1 is not None
            assert bike2 is not None

            db.session.add_all(
                [
                    DistanceWorkout(
                        type=WorkoutType.BIKING,
                        name='Workout Bike 1',
                        start_time=datetime(year=2025, month=6, day=1, hour=10, minute=0, second=0),
                        duration=3600,
                        distance=10 * 1000,
                        average_heart_rate=120,
                        elevation_sum=10,
                        user_id=user.id,
                        custom_fields={},
                        equipment=[bike1],
                    ),
                    DistanceWorkout(
                        type=WorkoutType.BIKING,
                        name='Workout Bike 2',
                        start_time=datetime(year=2025, month=6, day=2, hour=10, minute=0, second=0),
                        duration=3600,
                        distance=25 * 1000,
                        average_heart_rate=120,
                        elevation_sum=10,
                        user_id=user.id,
                        custom_fields={},
                        equipment=[bike2],
                    ),
                ]
            )
            db.session.commit()

            distance = DistanceWorkoutService.get_distance_between_dates(
                user.id,
                datetime(year=2025, month=1, day=1),
                datetime(year=2025, month=12, day=31),
                [WorkoutType.BIKING],
                equipmentId=bike1.id,
            )

            assert distance == 10 * 1000
