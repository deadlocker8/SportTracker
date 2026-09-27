from datetime import datetime

import pytest
from flask_login import FlaskLoginClient, login_user

from sporttracker.db import db
from sporttracker.gpx.GpxMetadataEntity import GpxMetadata
from sporttracker.longDistanceTour.LongDistanceTourEntity import (
    LongDistanceTour,
    LongDistanceTourPlannedTourAssociation,
)
from sporttracker.plannedTour.PlannedTourEntity import PlannedTour
from sporttracker.plannedTour.PlannedTourFilterStateEntity import PlannedTourFilterState
from sporttracker.plannedTour.PlannedTourService import PlannedTourService
from sporttracker.plannedTour.TravelDirection import TravelDirection
from sporttracker.plannedTour.TravelType import TravelType
from sporttracker.user.UserEntity import Language, User, create_user
from sporttracker.workout.distance.DistanceWorkoutEntity import DistanceWorkout
from sporttracker.workout.WorkoutType import WorkoutType
from tests.TestConstants import TEST_PASSWORD, TEST_USERNAME

TEST_USERNAME_2 = 'test_user_2'


@pytest.fixture(autouse=True)
def prepare_test_data(app):
    app.test_client_class = FlaskLoginClient

    with app.app_context():
        create_user(TEST_USERNAME, TEST_PASSWORD, False, Language.ENGLISH, 2026)
        create_user(TEST_USERNAME_2, TEST_PASSWORD, False, Language.ENGLISH, 2026)


class TestPlannedTourService:
    @staticmethod
    def __get_user_by_username(username: str) -> User:
        user = User.query.filter(User.username == username).first()
        if user is None:
            raise ValueError(f'Could not find user with username {username}')
        return user

    @staticmethod
    def __create_gpx_metadata(length: float) -> GpxMetadata:
        gpxMetadata = GpxMetadata(length=length)
        db.session.add(gpxMetadata)
        db.session.commit()
        return gpxMetadata

    @staticmethod
    def __create_planned_tour(
        name: str,
        user_id: int,
        shared_users: list[User],
        workoutType: WorkoutType = WorkoutType.BIKING,
        arrival_method: TravelType = TravelType.NONE,
        departure_method: TravelType = TravelType.NONE,
        direction: TravelDirection = TravelDirection.ROUNDTRIP,
        gpx_metadata_id: int | None = None,
    ) -> PlannedTour:
        plannedTour = PlannedTour(
            name=name,
            type=workoutType,
            user_id=user_id,
            creation_date=datetime.now(),
            last_edit_date=datetime.now(),
            last_edit_user_id=user_id,
            gpx_metadata_id=gpx_metadata_id,
            shared_users=shared_users,
            arrival_method=arrival_method,
            departure_method=departure_method,
            direction=direction,
            share_code=None,
        )
        db.session.add(plannedTour)
        db.session.commit()
        return plannedTour

    @staticmethod
    def __create_distance_workout(user: User, plannedTour: PlannedTour) -> DistanceWorkout:
        workout = DistanceWorkout(
            type=WorkoutType.BIKING,
            name='Dummy Workout',
            start_time=datetime(year=2026, month=8, day=15, hour=22, minute=1, second=0),
            duration=3600,
            distance=23 * 1000,
            average_heart_rate=130,
            elevation_sum=16,
            user_id=user.id,
            custom_fields={},
            planned_tour=plannedTour,
        )
        db.session.add(workout)
        db.session.commit()
        return workout

    @staticmethod
    def __create_long_distance_tour(
        name: str, user_id: int, shared_users: list[User], plannedTour: PlannedTour | None = None
    ) -> LongDistanceTour:
        longDistanceTour = LongDistanceTour(
            name=name,
            type=WorkoutType.BIKING,
            user_id=user_id,
            creation_date=datetime.now(),
            last_edit_date=datetime.now(),
            last_edit_user_id=user_id,
            shared_users=shared_users,
            linked_planned_tours=[],
        )
        db.session.add(longDistanceTour)
        db.session.commit()

        if plannedTour is not None:
            association = LongDistanceTourPlannedTourAssociation(
                long_distance_tour_id=longDistanceTour.id, planned_tour_id=plannedTour.id, order=0
            )
            db.session.add(association)
            db.session.commit()

        return longDistanceTour

    @staticmethod
    def __create_filter_state(
        is_own_tours_active: bool = True,
        is_shared_with_others_active: bool = True,
        is_shared_by_others_active: bool = True,
    ) -> PlannedTourFilterState:
        plannedTourFilterState = PlannedTourFilterState()
        plannedTourFilterState.reset()
        plannedTourFilterState.is_own_tours_active = is_own_tours_active  # type: ignore[assignment]
        plannedTourFilterState.is_shared_with_others_active = is_shared_with_others_active  # type: ignore[assignment]
        plannedTourFilterState.is_shared_by_others_active = is_shared_by_others_active  # type: ignore[assignment]
        return plannedTourFilterState

    @staticmethod
    def __get_tour_ids(filterState: PlannedTourFilterState, workoutTypes: list[WorkoutType] | None = None) -> set[int]:
        if workoutTypes is None:
            workoutTypes = WorkoutType.get_distance_workout_types()

        tours = PlannedTourService.get_planned_tours_filtered(workoutTypes, filterState)
        return {tour.id for tour in tours}

    def __create_share_status_tours(self, me: User, other: User) -> tuple[PlannedTour, PlannedTour, PlannedTour]:
        privateTour = self.__create_planned_tour('private tour', me.id, [])
        sharedWithOthersTour = self.__create_planned_tour('shared with others tour', me.id, [other])
        sharedByOthersTour = self.__create_planned_tour('shared by others tour', other.id, [me])
        return privateTour, sharedWithOthersTour, sharedByOthersTour

    def test_get_planned_tours_filtered_by_share_status_all_active(self, app) -> None:
        with app.test_request_context():
            me = self.__get_user_by_username(TEST_USERNAME)
            other = self.__get_user_by_username(TEST_USERNAME_2)
            login_user(me, remember=False)

            privateTour, sharedWithOthersTour, sharedByOthersTour = self.__create_share_status_tours(me, other)

            filterState = self.__create_filter_state(True, True, True)

            assert self.__get_tour_ids(filterState) == {
                privateTour.id,
                sharedWithOthersTour.id,
                sharedByOthersTour.id,
            }

    def test_get_planned_tours_filtered_by_share_status_own_tours_only(self, app) -> None:
        with app.test_request_context():
            me = self.__get_user_by_username(TEST_USERNAME)
            other = self.__get_user_by_username(TEST_USERNAME_2)
            login_user(me, remember=False)

            privateTour, _, _ = self.__create_share_status_tours(me, other)

            filterState = self.__create_filter_state(True, False, False)

            assert self.__get_tour_ids(filterState) == {privateTour.id}

    def test_get_planned_tours_filtered_by_share_status_shared_with_others_only(self, app) -> None:
        with app.test_request_context():
            me = self.__get_user_by_username(TEST_USERNAME)
            other = self.__get_user_by_username(TEST_USERNAME_2)
            login_user(me, remember=False)

            _, sharedWithOthersTour, _ = self.__create_share_status_tours(me, other)

            filterState = self.__create_filter_state(False, True, False)

            assert self.__get_tour_ids(filterState) == {sharedWithOthersTour.id}

    def test_get_planned_tours_filtered_by_share_status_shared_by_others_only(self, app) -> None:
        with app.test_request_context():
            me = self.__get_user_by_username(TEST_USERNAME)
            other = self.__get_user_by_username(TEST_USERNAME_2)
            login_user(me, remember=False)

            _, _, sharedByOthersTour = self.__create_share_status_tours(me, other)

            filterState = self.__create_filter_state(False, False, True)

            assert self.__get_tour_ids(filterState) == {sharedByOthersTour.id}

    def test_get_planned_tours_filtered_by_share_status_own_tours_excludes_shared_ones(self, app) -> None:
        with app.test_request_context():
            me = self.__get_user_by_username(TEST_USERNAME)
            other = self.__get_user_by_username(TEST_USERNAME_2)
            login_user(me, remember=False)

            privateTour, sharedWithOthersTour, _ = self.__create_share_status_tours(me, other)

            ownAndSharedWithOthers = self.__create_filter_state(True, True, False)
            assert self.__get_tour_ids(ownAndSharedWithOthers) == {privateTour.id, sharedWithOthersTour.id}

    def test_get_planned_tours_filtered_by_share_status_none_active(self, app) -> None:
        with app.test_request_context():
            me = self.__get_user_by_username(TEST_USERNAME)
            other = self.__get_user_by_username(TEST_USERNAME_2)
            login_user(me, remember=False)

            self.__create_share_status_tours(me, other)

            filterState = self.__create_filter_state(False, False, False)

            assert self.__get_tour_ids(filterState) == set()

    def test_get_planned_tours_filtered_by_workout_type(self, app) -> None:
        with app.test_request_context():
            me = self.__get_user_by_username(TEST_USERNAME)
            login_user(me, remember=False)

            bikingTour = self.__create_planned_tour('biking tour', me.id, [], workoutType=WorkoutType.BIKING)
            self.__create_planned_tour('running tour', me.id, [], workoutType=WorkoutType.RUNNING)

            filterState = self.__create_filter_state()

            assert self.__get_tour_ids(filterState, [WorkoutType.BIKING]) == {bikingTour.id}

    def test_get_planned_tours_filtered_by_arrival_method(self, app) -> None:
        with app.test_request_context():
            me = self.__get_user_by_username(TEST_USERNAME)
            login_user(me, remember=False)

            trainTour = self.__create_planned_tour('train tour', me.id, [], arrival_method=TravelType.TRAIN)
            carTour = self.__create_planned_tour('car tour', me.id, [], arrival_method=TravelType.CAR)

            filterState = self.__create_filter_state()
            assert self.__get_tour_ids(filterState) == {trainTour.id, carTour.id}

            filterState.arrival_methods[TravelType.TRAIN.name] = False
            assert self.__get_tour_ids(filterState) == {carTour.id}

    def test_get_planned_tours_filtered_by_departure_method(self, app) -> None:
        with app.test_request_context():
            me = self.__get_user_by_username(TEST_USERNAME)
            login_user(me, remember=False)

            trainTour = self.__create_planned_tour('train tour', me.id, [], departure_method=TravelType.TRAIN)
            carTour = self.__create_planned_tour('car tour', me.id, [], departure_method=TravelType.CAR)

            filterState = self.__create_filter_state()
            assert self.__get_tour_ids(filterState) == {trainTour.id, carTour.id}

            filterState.departure_methods[TravelType.CAR.name] = False
            assert self.__get_tour_ids(filterState) == {trainTour.id}

    def test_get_planned_tours_filtered_by_direction(self, app) -> None:
        with app.test_request_context():
            me = self.__get_user_by_username(TEST_USERNAME)
            login_user(me, remember=False)

            singleTour = self.__create_planned_tour('single tour', me.id, [], direction=TravelDirection.SINGLE)
            roundtripTour = self.__create_planned_tour('roundtrip tour', me.id, [], direction=TravelDirection.ROUNDTRIP)

            filterState = self.__create_filter_state()
            assert self.__get_tour_ids(filterState) == {singleTour.id, roundtripTour.id}

            filterState.directions[TravelDirection.ROUNDTRIP.name] = False
            assert self.__get_tour_ids(filterState) == {singleTour.id}

    def test_get_planned_tours_filtered_by_name_filter(self, app) -> None:
        with app.test_request_context():
            me = self.__get_user_by_username(TEST_USERNAME)
            login_user(me, remember=False)

            alpsTour = self.__create_planned_tour('Tour through the Alps', me.id, [])
            berlinTour = self.__create_planned_tour('Tour to Berlin', me.id, [])

            filterState = self.__create_filter_state()
            assert self.__get_tour_ids(filterState) == {alpsTour.id, berlinTour.id}

            filterState.name_filter = 'the alps'  # type: ignore[assignment]
            assert self.__get_tour_ids(filterState) == {alpsTour.id}

            filterState.name_filter = 'TOUR TO'  # type: ignore[assignment]
            assert self.__get_tour_ids(filterState) == {berlinTour.id}

            filterState.name_filter = 'nothing matches this'  # type: ignore[assignment]
            assert self.__get_tour_ids(filterState) == set()

    def test_get_planned_tours_filtered_by_minimum_distance(self, app) -> None:
        with app.test_request_context():
            me = self.__get_user_by_username(TEST_USERNAME)
            login_user(me, remember=False)

            self.__create_planned_tour(
                'short tour', me.id, [], gpx_metadata_id=self.__create_gpx_metadata(10 * 1000).id
            )
            longTour = self.__create_planned_tour(
                'long tour', me.id, [], gpx_metadata_id=self.__create_gpx_metadata(50 * 1000).id
            )

            filterState = self.__create_filter_state()
            filterState.minimum_distance = 20 * 1000  # type: ignore[assignment]

            assert self.__get_tour_ids(filterState) == {longTour.id}

    def test_get_planned_tours_filtered_by_maximum_distance(self, app) -> None:
        with app.test_request_context():
            me = self.__get_user_by_username(TEST_USERNAME)
            login_user(me, remember=False)

            shortTour = self.__create_planned_tour(
                'short tour', me.id, [], gpx_metadata_id=self.__create_gpx_metadata(10 * 1000).id
            )
            self.__create_planned_tour('long tour', me.id, [], gpx_metadata_id=self.__create_gpx_metadata(50 * 1000).id)

            filterState = self.__create_filter_state()
            filterState.maximum_distance = 20 * 1000  # type: ignore[assignment]

            assert self.__get_tour_ids(filterState) == {shortTour.id}

    def test_get_planned_tours_filtered_by_distance_boundaries_are_inclusive(self, app) -> None:
        with app.test_request_context():
            me = self.__get_user_by_username(TEST_USERNAME)
            login_user(me, remember=False)

            tour = self.__create_planned_tour(
                'boundary tour', me.id, [], gpx_metadata_id=self.__create_gpx_metadata(20 * 1000).id
            )

            filterState = self.__create_filter_state()
            filterState.minimum_distance = 20 * 1000  # type: ignore[assignment]
            assert self.__get_tour_ids(filterState) == {tour.id}

            filterState.maximum_distance = 20 * 1000  # type: ignore[assignment]
            assert self.__get_tour_ids(filterState) == {tour.id}

    def test_get_planned_tours_filtered_by_distance_ignores_tours_without_gpx_metadata(self, app) -> None:
        with app.test_request_context():
            me = self.__get_user_by_username(TEST_USERNAME)
            login_user(me, remember=False)

            tourWithGpx = self.__create_planned_tour(
                'with gpx', me.id, [], gpx_metadata_id=self.__create_gpx_metadata(20 * 1000).id
            )
            tourWithoutGpx = self.__create_planned_tour('without gpx', me.id, [])

            filterState = self.__create_filter_state()
            assert self.__get_tour_ids(filterState) == {tourWithGpx.id, tourWithoutGpx.id}

            filterState.minimum_distance = 1  # type: ignore[assignment]
            assert self.__get_tour_ids(filterState) == {tourWithGpx.id}

    def test_get_planned_tours_filtered_by_status_done(self, app) -> None:
        with app.test_request_context():
            me = self.__get_user_by_username(TEST_USERNAME)
            login_user(me, remember=False)

            doneTour = self.__create_planned_tour('done tour', me.id, [])
            self.__create_planned_tour('todo tour', me.id, [])
            self.__create_distance_workout(me, doneTour)

            filterState = self.__create_filter_state()
            filterState.is_done_selected = True  # type: ignore[assignment]
            filterState.is_todo_selected = False  # type: ignore[assignment]

            assert self.__get_tour_ids(filterState) == {doneTour.id}

    def test_get_planned_tours_filtered_by_status_todo(self, app) -> None:
        with app.test_request_context():
            me = self.__get_user_by_username(TEST_USERNAME)
            login_user(me, remember=False)

            doneTour = self.__create_planned_tour('done tour', me.id, [])
            todoTour = self.__create_planned_tour('todo tour', me.id, [])
            self.__create_distance_workout(me, doneTour)

            filterState = self.__create_filter_state()
            filterState.is_done_selected = False  # type: ignore[assignment]
            filterState.is_todo_selected = True  # type: ignore[assignment]

            assert self.__get_tour_ids(filterState) == {todoTour.id}

    def test_get_planned_tours_filtered_by_long_distance_tours_include(self, app) -> None:
        with app.test_request_context():
            me = self.__get_user_by_username(TEST_USERNAME)
            other = self.__get_user_by_username(TEST_USERNAME_2)
            login_user(me, remember=False)

            tourWithOwnLdt = self.__create_planned_tour('tour with own ldt', me.id, [])
            self.__create_long_distance_tour('own ldt tour', me.id, [], tourWithOwnLdt)

            tourWithSharedLdt = self.__create_planned_tour('tour with shared ldt', me.id, [])
            self.__create_long_distance_tour('shared ldt tour', other.id, [me], tourWithSharedLdt)

            tourWithInaccessibleLdt = self.__create_planned_tour('tour with inaccessible ldt', me.id, [])
            self.__create_long_distance_tour('inaccessible ldt tour', other.id, [], tourWithInaccessibleLdt)

            tourWithoutLdt = self.__create_planned_tour('tour without ldt', me.id, [])

            filterState = self.__create_filter_state()
            filterState.is_long_distance_tours_include_selected = True  # type: ignore[assignment]
            filterState.is_long_distance_tours_exclude_selected = False  # type: ignore[assignment]

            tourIds = self.__get_tour_ids(filterState)
            assert tourIds == {tourWithOwnLdt.id, tourWithSharedLdt.id}
            assert tourWithInaccessibleLdt.id not in tourIds
            assert tourWithoutLdt.id not in tourIds

    def test_get_planned_tours_filtered_by_long_distance_tours_exclude(self, app) -> None:
        with app.test_request_context():
            me = self.__get_user_by_username(TEST_USERNAME)
            other = self.__get_user_by_username(TEST_USERNAME_2)
            login_user(me, remember=False)

            tourWithOwnLdt = self.__create_planned_tour('tour with own ldt', me.id, [])
            self.__create_long_distance_tour('own ldt tour', me.id, [], tourWithOwnLdt)

            tourWithInaccessibleLdt = self.__create_planned_tour('tour with inaccessible ldt', me.id, [])
            self.__create_long_distance_tour('inaccessible ldt tour', other.id, [], tourWithInaccessibleLdt)

            tourWithoutLdt = self.__create_planned_tour('tour without ldt', me.id, [])

            filterState = self.__create_filter_state()
            filterState.is_long_distance_tours_include_selected = False  # type: ignore[assignment]
            filterState.is_long_distance_tours_exclude_selected = True  # type: ignore[assignment]

            tourIds = self.__get_tour_ids(filterState)
            assert tourIds == {tourWithInaccessibleLdt.id, tourWithoutLdt.id}
            assert tourWithOwnLdt.id not in tourIds

    def test_get_planned_tours_filtered_returns_tours_sorted_naturally_case_insensitive(self, app) -> None:
        with app.test_request_context():
            me = self.__get_user_by_username(TEST_USERNAME)
            login_user(me, remember=False)

            for name in ['Tour 10', 'Tour 2', 'apple', 'Banana']:
                self.__create_planned_tour(name, me.id, [])

            filterState = self.__create_filter_state()
            tours = PlannedTourService.get_planned_tours_filtered(WorkoutType.get_distance_workout_types(), filterState)

            assert [tour.name for tour in tours] == ['apple', 'Banana', 'Tour 2', 'Tour 10']
