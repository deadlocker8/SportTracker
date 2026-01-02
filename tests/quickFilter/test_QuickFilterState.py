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
        quickFilterState.workout_types = {}
        assert len(quickFilterState.workout_types) == 0

        quickFilterState.update_missing_values([])
        assert quickFilterState.get_workout_types() == {
            WorkoutType.BIKING: True,
            WorkoutType.RUNNING: True,
            WorkoutType.HIKING: True,
            WorkoutType.FITNESS: True,
        }

    def test_update_missing_values_years(self) -> None:
        quickFilterState = QuickFilterState()
        quickFilterState.workout_types = {}
        quickFilterState.years = {2024: False}

        quickFilterState.update_missing_values([2024, 2025, 2026])
        assert quickFilterState.years == {
            2024: False,
            2025: True,
            2026: True,
        }

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
