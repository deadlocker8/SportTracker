from sporttracker.logic.model.filterStates.MaintenanceFilterState import MaintenanceFilterState


class TestMaintenanceFilterState:
    def test_reset(self) -> None:
        maintenanceFilterState = MaintenanceFilterState()
        maintenanceFilterState.custom_workout_field_id = 15
        maintenanceFilterState.custom_workout_field_value = 'Test'  # type: ignore[assignment]

        assert maintenanceFilterState.custom_workout_field_id == 15
        assert maintenanceFilterState.custom_workout_field_value == 'Test'

        maintenanceFilterState.reset()

        assert maintenanceFilterState.custom_workout_field_id is None
        assert maintenanceFilterState.custom_workout_field_value is None

    def test_is_active(self) -> None:
        maintenanceFilterState = MaintenanceFilterState()

        assert maintenanceFilterState.is_active() is False

        maintenanceFilterState.custom_workout_field_id = 15
        maintenanceFilterState.custom_workout_field_value = 'Test'  # type: ignore[assignment]

        assert maintenanceFilterState.is_active() is True
