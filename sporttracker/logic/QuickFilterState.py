from __future__ import annotations

import json

from flask import session

from sporttracker.logic.model.WorkoutType import WorkoutType


class QuickFilterState:
    def __init__(self) -> None:
        self._states = {workoutType: True for workoutType in WorkoutType}

    def toggle_state(self, workoutType):
        self._states[workoutType] = not self._states[workoutType]

    def get_states(self) -> dict[WorkoutType, bool]:
        return dict(sorted(self._states.items(), key=lambda entry: entry[0].order))

    def set_states(self, states: dict[WorkoutType, bool]) -> None:
        self._states = states

    def get_active_types(self) -> list[WorkoutType]:
        return [workoutType for workoutType, isActive in self._states.items() if isActive]

    def get_active_distance_workout_types(self) -> list[WorkoutType]:
        return [
            workoutType
            for workoutType, isActive in self._states.items()
            if isActive and workoutType in WorkoutType.get_distance_workout_types()
        ]

    def to_json(self) -> str:
        return json.dumps(
            {workoutType.name: isActive for workoutType, isActive in self._states.items()}
        )

    @staticmethod
    def from_json(jsonString: str) -> QuickFilterState:
        states = {
            WorkoutType(workoutType): isActive  # type: ignore[call-arg]
            for workoutType, isActive in json.loads(jsonString).items()
        }
        quickFilterState = QuickFilterState()
        quickFilterState.set_states(states)
        return quickFilterState


def get_quick_filter_state_from_session() -> QuickFilterState:
    if 'quickFilterState' not in session:
        session['quickFilterState'] = QuickFilterState().to_json()

    quickFilterState = QuickFilterState.from_json(session['quickFilterState'])

    # check if any workout types are missing and update session accordingly
    if quickFilterState.get_states().keys() != QuickFilterState().get_states().keys():
        session['quickFilterState'] = QuickFilterState().to_json()

    return QuickFilterState.from_json(session['quickFilterState'])
