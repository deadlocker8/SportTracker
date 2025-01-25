from __future__ import annotations

import json

from flask import session

from sporttracker.logic.model.SportType import SportType


class QuickFilterState:
    def __init__(self) -> None:
        self._states = {sportType: True for sportType in SportType}

    def toggle_state(self, sportType):
        self._states[sportType] = not self._states[sportType]

    def get_states(self) -> dict[SportType, bool]:
        return dict(sorted(self._states.items(), key=lambda entry: entry[0].order))

    def set_states(self, states: dict[SportType, bool]) -> None:
        self._states = states

    def get_active_types(self) -> list[SportType]:
        return [sportType for sportType, isActive in self._states.items() if isActive]

    def get_active_distance_sport_types(self) -> list[SportType]:
        return [
            sportType
            for sportType, isActive in self._states.items()
            if isActive and sportType in SportType.get_distance_sport_types()
        ]

    def to_json(self) -> str:
        return json.dumps(
            {sportType.name: isActive for sportType, isActive in self._states.items()}
        )

    @staticmethod
    def from_json(jsonString: str) -> QuickFilterState:
        states = {
            SportType(sportType): isActive  # type: ignore[call-arg]
            for sportType, isActive in json.loads(jsonString).items()
        }
        quickFilterState = QuickFilterState()
        quickFilterState.set_states(states)
        return quickFilterState


def get_quick_filter_state_from_session() -> QuickFilterState:
    if 'quickFilterState' not in session:
        session['quickFilterState'] = QuickFilterState().to_json()

    quickFilterState = QuickFilterState.from_json(session['quickFilterState'])

    # check if any sport types are missing and update session accordingly
    if quickFilterState.get_states().keys() != QuickFilterState().get_states().keys():
        session['quickFilterState'] = QuickFilterState().to_json()

    return QuickFilterState.from_json(session['quickFilterState'])
