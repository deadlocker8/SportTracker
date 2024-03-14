from __future__ import annotations

import json

from flask import session

from sporttracker.logic.model.Track import TrackType


class QuickFilterState:
    def __init__(self) -> None:
        self._states = {trackType: True for trackType in TrackType}

    def toggle_state(self, trackType):
        self._states[trackType] = not self._states[trackType]

    def get_states(self) -> dict[TrackType, bool]:
        return dict(sorted(self._states.items(), key=lambda entry: entry[0].order))

    def set_states(self, states: dict[TrackType, bool]) -> None:
        self._states = states

    def get_active_types(self) -> list[TrackType]:
        return [trackType for trackType, isActive in self._states.items() if isActive]

    def to_json(self) -> str:
        return json.dumps(
            {trackType.name: isActive for trackType, isActive in self._states.items()}
        )

    @staticmethod
    def from_json(jsonString: str) -> QuickFilterState:
        states = {
            TrackType(trackType): isActive  # type: ignore[call-arg]
            for trackType, isActive in json.loads(jsonString).items()
        }
        quickFilterState = QuickFilterState()
        quickFilterState.set_states(states)
        return quickFilterState


def get_quick_filter_state_from_session() -> QuickFilterState:
    if 'quickFilterState' not in session:
        session['quickFilterState'] = QuickFilterState().to_json()

    return QuickFilterState.from_json(session['quickFilterState'])
