from sporttracker.workout.WorkoutType import WorkoutType
from sporttracker.quickFilter.QuickFilterStateEntity import QuickFilterState


class TestQuickFilterState:
    def test_reset(self) -> None:
        quickFilterState = QuickFilterState()
        quickFilterState.update(
            {
                WorkoutType.BIKING: False,
                WorkoutType.RUNNING: False,
                WorkoutType.HIKING: False,
                WorkoutType.FITNESS: False,
            },
            [2025, 2026],
        )
        quickFilterState.years = {
            2025: False,
            2026: True,
        }

        assert quickFilterState.get_workout_types() == {
            WorkoutType.BIKING: False,
            WorkoutType.RUNNING: False,
            WorkoutType.HIKING: False,
            WorkoutType.FITNESS: False,
        }

        quickFilterState.reset([2025, 2026])
        assert quickFilterState.get_workout_types() == {
            WorkoutType.BIKING: True,
            WorkoutType.RUNNING: True,
            WorkoutType.HIKING: True,
            WorkoutType.FITNESS: True,
        }

        assert quickFilterState.years == {
            2025: True,
            2026: True,
        }

    def test_update_missing_values_workout_types(self) -> None:
        quickFilterState = QuickFilterState()
        quickFilterState.workout_types = {WorkoutType.BIKING.name: False}
        assert len(quickFilterState.workout_types) == 1

        isUpdated = quickFilterState.update_missing_values([])
        assert isUpdated is True
        assert quickFilterState.get_workout_types() == {
            WorkoutType.BIKING: False,
            WorkoutType.RUNNING: True,
            WorkoutType.HIKING: True,
            WorkoutType.FITNESS: True,
        }

    def test_update_missing_values_years(self) -> None:
        quickFilterState = QuickFilterState()
        quickFilterState.workout_types = {}
        quickFilterState.years = {2023: True, 2024: False}

        isUpdated = quickFilterState.update_missing_values([2024, 2025, 2026])
        assert isUpdated is True
        assert quickFilterState.years == {
            2024: False,
            2025: True,
            2026: True,
        }

    def test_update_missing_values_removes_stale_years(self) -> None:
        quickFilterState = QuickFilterState()
        quickFilterState.workout_types = {}
        quickFilterState.years = {2020: True, 2021: True, 2022: True}

        isUpdated = quickFilterState.update_missing_values([2021])
        assert isUpdated is True
        assert quickFilterState.years == {2021: True}

    def test_update_missing_values_returns_false_when_nothing_missing(self) -> None:
        quickFilterState = QuickFilterState()
        quickFilterState.workout_types = {
            WorkoutType.BIKING.name: True,
            WorkoutType.RUNNING.name: False,
            WorkoutType.HIKING.name: True,
            WorkoutType.FITNESS.name: False,
        }
        quickFilterState.years = {2025: True, 2026: False}

        isUpdated = quickFilterState.update_missing_values([2025, 2026])
        assert isUpdated is False
        assert quickFilterState.get_workout_types() == {
            WorkoutType.BIKING: True,
            WorkoutType.RUNNING: False,
            WorkoutType.HIKING: True,
            WorkoutType.FITNESS: False,
        }
        assert quickFilterState.years == {2025: True, 2026: False}

    def test_update_missing_values_with_empty_available_years(self) -> None:
        quickFilterState = QuickFilterState()
        quickFilterState.workout_types = {}
        quickFilterState.years = {}

        isUpdated = quickFilterState.update_missing_values([])
        assert isUpdated is True
        assert quickFilterState.get_workout_types() == {
            WorkoutType.BIKING: True,
            WorkoutType.RUNNING: True,
            WorkoutType.HIKING: True,
            WorkoutType.FITNESS: True,
        }
        assert quickFilterState.years == {}

    def test_toggle_workout_type(self) -> None:
        quickFilterState = QuickFilterState()
        quickFilterState.reset([])

        quickFilterState.toggle_workout_type(WorkoutType.BIKING)

        assert quickFilterState.get_workout_types() == {
            WorkoutType.BIKING: False,
            WorkoutType.RUNNING: True,
            WorkoutType.HIKING: True,
            WorkoutType.FITNESS: True,
        }

    def test_enable_all_workout_types(self) -> None:
        quickFilterState = QuickFilterState()
        quickFilterState.reset([])
        quickFilterState.workout_types = {
            WorkoutType.BIKING: True,
            WorkoutType.RUNNING: True,
            WorkoutType.HIKING: True,
            WorkoutType.FITNESS: True,
        }

        quickFilterState.enable_all_workout_types()

        assert quickFilterState.get_workout_types() == {
            WorkoutType.BIKING: True,
            WorkoutType.RUNNING: True,
            WorkoutType.HIKING: True,
            WorkoutType.FITNESS: True,
        }

    def test_get_active_workout_types(self) -> None:
        quickFilterState = QuickFilterState()
        quickFilterState.update(
            {
                WorkoutType.BIKING: False,
                WorkoutType.RUNNING: True,
                WorkoutType.HIKING: False,
                WorkoutType.FITNESS: False,
            },
            [],
        )

        assert quickFilterState.get_active_workout_types() == [WorkoutType.RUNNING]

    def test_get_active_distance_workout_types(self) -> None:
        quickFilterState = QuickFilterState()
        quickFilterState.update(
            {
                WorkoutType.BIKING: False,
                WorkoutType.RUNNING: True,
                WorkoutType.HIKING: False,
                WorkoutType.FITNESS: True,
            },
            [],
        )

        assert quickFilterState.get_active_distance_workout_types() == [WorkoutType.RUNNING]

    def test_update_sets_workout_types(self) -> None:
        quickFilterState = QuickFilterState()
        quickFilterState.update(
            {
                WorkoutType.BIKING: True,
                WorkoutType.RUNNING: False,
                WorkoutType.HIKING: True,
                WorkoutType.FITNESS: False,
            },
            [],
        )

        assert quickFilterState.workout_types == {
            'BIKING': True,
            'RUNNING': False,
            'HIKING': True,
            'FITNESS': False,
        }

    def test_update_initializes_years_when_none(self) -> None:
        quickFilterState = QuickFilterState()
        quickFilterState.years = None

        quickFilterState.update({}, [2024, 2025, 2026])

        assert quickFilterState.years == {
            2024: True,
            2025: True,
            2026: True,
        }

    def test_update_updates_existing_years(self) -> None:
        quickFilterState = QuickFilterState()
        quickFilterState.years = {2024: True, 2025: True, 2026: True}

        quickFilterState.update({}, [2025, 2026])

        assert quickFilterState.years == {
            2024: False,
            2025: True,
            2026: True,
        }

    def test_update_does_not_add_missing_years(self) -> None:
        quickFilterState = QuickFilterState()
        quickFilterState.years = {2025: True}

        quickFilterState.update({}, [2024, 2025, 2026])

        assert quickFilterState.years == {
            2025: True,
        }
