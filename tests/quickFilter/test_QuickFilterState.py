from datetime import date

from sporttracker.quickFilter.QuickFilterStateEntity import QuickFilterState
from sporttracker.workout.WorkoutType import WorkoutType


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
            '2025': False,
            '2026': True,
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
            '2025': True,
            '2026': True,
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
        quickFilterState.years = {'2023': True, '2024': False}

        isUpdated = quickFilterState.update_missing_values([2024, 2025, 2026])
        assert isUpdated is True
        assert quickFilterState.years == {
            '2024': False,
            '2025': True,
            '2026': True,
        }

    def test_update_missing_values_removes_stale_years(self) -> None:
        quickFilterState = QuickFilterState()
        quickFilterState.workout_types = {}
        quickFilterState.years = {'2020': True, '2021': True, '2022': True}

        isUpdated = quickFilterState.update_missing_values([2021])
        assert isUpdated is True
        assert quickFilterState.years == {'2021': True}

    def test_update_missing_values_returns_false_when_nothing_missing(self) -> None:
        quickFilterState = QuickFilterState()
        quickFilterState.workout_types = {
            WorkoutType.BIKING.name: True,
            WorkoutType.RUNNING.name: False,
            WorkoutType.HIKING.name: True,
            WorkoutType.FITNESS.name: False,
        }
        quickFilterState.years = {'2025': True, '2026': False}

        isUpdated = quickFilterState.update_missing_values([2025, 2026])
        assert isUpdated is False
        assert quickFilterState.get_workout_types() == {
            WorkoutType.BIKING: True,
            WorkoutType.RUNNING: False,
            WorkoutType.HIKING: True,
            WorkoutType.FITNESS: False,
        }
        assert quickFilterState.years == {'2025': True, '2026': False}

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
            '2024': True,
            '2025': True,
            '2026': True,
        }

    def test_update_updates_existing_years(self) -> None:
        quickFilterState = QuickFilterState()
        quickFilterState.years = {'2024': True, '2025': True, '2026': True}

        quickFilterState.update({}, [2025, 2026])

        assert quickFilterState.years == {
            '2024': False,
            '2025': True,
            '2026': True,
        }

    def test_update_does_not_add_missing_years(self) -> None:
        quickFilterState = QuickFilterState()
        quickFilterState.years = {'2025': True}

        quickFilterState.update({}, [2024, 2025, 2026])

        assert quickFilterState.years == {
            '2025': True,
        }

    def test_get_effective_date_ranges_empty_without_any_filter(self) -> None:
        quickFilterState = QuickFilterState()
        quickFilterState.workout_types = {}
        quickFilterState.years = {}

        assert quickFilterState.get_effective_date_ranges() is None

    def test_get_effective_date_ranges_none_when_all_years_active(self) -> None:
        quickFilterState = QuickFilterState()
        quickFilterState.workout_types = {}
        quickFilterState.years = {'2025': True, '2026': True}

        assert quickFilterState.get_effective_date_ranges() is None

    def test_get_effective_date_ranges_empty_without_active_years(self) -> None:
        quickFilterState = QuickFilterState()
        quickFilterState.workout_types = {}
        quickFilterState.years = {'2020': False, '2021': False, '2022': False}

        assert quickFilterState.get_effective_date_ranges() == []

    def test_get_effective_date_ranges_single_year(self) -> None:
        quickFilterState = QuickFilterState()
        quickFilterState.workout_types = {}
        quickFilterState.years = {'2025': True, '2026': False}

        assert quickFilterState.get_effective_date_ranges() == [(date(2025, 1, 1), date(2025, 12, 31))]

    def test_get_effective_date_ranges_continuous_years(self) -> None:
        quickFilterState = QuickFilterState()
        quickFilterState.workout_types = {}
        quickFilterState.years = {'2024': True, '2025': True, '2026': False}

        assert quickFilterState.get_effective_date_ranges() == [(date(2024, 1, 1), date(2025, 12, 31))]

    def test_get_effective_date_ranges_non_continuous_years(self) -> None:
        quickFilterState = QuickFilterState()
        quickFilterState.workout_types = {}
        quickFilterState.years = {'2020': True, '2021': False, '2022': True}

        assert quickFilterState.get_effective_date_ranges() == [
            (date(2020, 1, 1), date(2020, 12, 31)),
            (date(2022, 1, 1), date(2022, 12, 31)),
        ]

    def test_get_effective_date_ranges_prefers_date_range_over_years(self) -> None:
        quickFilterState = QuickFilterState()
        quickFilterState.workout_types = {}
        quickFilterState.years = {'2020': True, '2021': False, '2022': True}
        quickFilterState.set_date_filter(date(2022, 5, 1), date(2022, 6, 15))

        assert quickFilterState.get_effective_date_ranges() == [(date(2022, 5, 1), date(2022, 6, 15))]

    def test_is_date_filter_active(self) -> None:
        quickFilterState = QuickFilterState()
        quickFilterState.workout_types = {}
        quickFilterState.years = {'2025': True}

        assert quickFilterState.is_date_filter_active() is False

        quickFilterState.set_date_filter(date(2025, 1, 1), date(2025, 12, 31))
        assert quickFilterState.is_date_filter_active() is True

        quickFilterState.clear_date_filter()
        assert quickFilterState.is_date_filter_active() is False

    def test_set_date_filter(self) -> None:
        quickFilterState = QuickFilterState()
        quickFilterState.workout_types = {}
        quickFilterState.years = {'2025': True}

        quickFilterState.set_date_filter(date(2025, 6, 1), date(2025, 8, 31))

        assert quickFilterState.get_date_range() == (date(2025, 6, 1), date(2025, 8, 31))

    def test_get_date_range_is_none_when_not_set(self) -> None:
        quickFilterState = QuickFilterState()
        quickFilterState.workout_types = {}
        quickFilterState.years = {'2025': True}

        assert quickFilterState.get_date_range() is None

    def test_clear_date_filter(self) -> None:
        quickFilterState = QuickFilterState()
        quickFilterState.workout_types = {}
        quickFilterState.years = {'2025': True}
        quickFilterState.set_date_filter(date(2025, 1, 1), date(2025, 12, 31))

        quickFilterState.clear_date_filter()

        assert quickFilterState.get_date_range() is None

    def test_is_any_filter_active_with_date_range(self) -> None:
        quickFilterState = QuickFilterState()
        quickFilterState.workout_types = {}
        quickFilterState.years = {'2025': True, '2026': True}
        quickFilterState.set_date_filter(date(2026, 1, 1), date(2026, 1, 31))

        assert quickFilterState.is_any_filter_active() is True

    def test_is_any_filter_active_with_inactive_years(self) -> None:
        quickFilterState = QuickFilterState()
        quickFilterState.workout_types = {}
        quickFilterState.years = {'2025': True, '2026': False}

        assert quickFilterState.is_any_filter_active() is True

    def test_is_any_filter_active_when_no_filter(self) -> None:
        quickFilterState = QuickFilterState()
        quickFilterState.workout_types = {}
        quickFilterState.years = {'2025': True, '2026': True}

        assert quickFilterState.is_any_filter_active() is False
