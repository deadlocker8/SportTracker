from sporttracker.workout.WorkoutType import WorkoutType
from sporttracker.logic.model.filterStates.QuickFilterState import QuickFilterState


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
            [],
        )

        assert quickFilterState.get_workout_types() == {
            WorkoutType.BIKING: False,
            WorkoutType.RUNNING: False,
            WorkoutType.HIKING: False,
            WorkoutType.FITNESS: False,
        }

        quickFilterState.reset([2024, 2025])
        assert quickFilterState.get_workout_types() == {
            WorkoutType.BIKING: True,
            WorkoutType.RUNNING: True,
            WorkoutType.HIKING: True,
            WorkoutType.FITNESS: True,
        }

    def test_update_missing_values(self) -> None:
        quickFilterState = QuickFilterState()
        quickFilterState.workout_types = {}
        assert len(quickFilterState.workout_types) == 0

        quickFilterState.update_missing_values()
        assert quickFilterState.get_workout_types() == {
            WorkoutType.BIKING: True,
            WorkoutType.RUNNING: True,
            WorkoutType.HIKING: True,
            WorkoutType.FITNESS: True,
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

    def test_disable_all_workout_types(self) -> None:
        quickFilterState = QuickFilterState()
        quickFilterState.reset([])

        quickFilterState.disable_all_workout_types()

        assert quickFilterState.get_workout_types() == {
            WorkoutType.BIKING: False,
            WorkoutType.RUNNING: False,
            WorkoutType.HIKING: False,
            WorkoutType.FITNESS: False,
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
