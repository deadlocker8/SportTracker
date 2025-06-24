from __future__ import annotations

import json

from flask import session


class MaintenanceFilterState:
    SESSION_ATTRIBUTE_NAME = 'maintenanceFilterState'

    def __init__(self) -> None:
        self._custom_workout_field_id: int | None = None
        self._custom_workout_field_value: str | None = None

    def update(self, custom_workout_field_id: int | None, custom_workout_field_value: str | None):
        self._custom_workout_field_id = custom_workout_field_id
        self._custom_workout_field_value = custom_workout_field_value

    def get_custom_workout_field_id(self) -> int | None:
        return self._custom_workout_field_id

    def get_custom_workout_field_value(self) -> str | None:
        return self._custom_workout_field_value

    def is_active(self) -> bool:
        return self._custom_workout_field_id is not None and self._custom_workout_field_value is not None

    def to_json(self) -> str:
        return json.dumps(
            {
                'customWorkoutFieldId': self._custom_workout_field_id,
                'customWorkoutFieldValue': self._custom_workout_field_value,
            }
        )

    @staticmethod
    def from_json(jsonString: str) -> MaintenanceFilterState:
        jsonData = json.loads(jsonString)

        maintenanceFilterState = MaintenanceFilterState()
        maintenanceFilterState.update(
            None if jsonData['customWorkoutFieldId'] is None else int(jsonData['customWorkoutFieldId']),
            jsonData['customWorkoutFieldValue'],
        )
        return maintenanceFilterState


def get_maintenances_filter_state_from_session() -> MaintenanceFilterState:
    if MaintenanceFilterState.SESSION_ATTRIBUTE_NAME not in session:
        session[MaintenanceFilterState.SESSION_ATTRIBUTE_NAME] = MaintenanceFilterState().to_json()

    return MaintenanceFilterState.from_json(session[MaintenanceFilterState.SESSION_ATTRIBUTE_NAME])
