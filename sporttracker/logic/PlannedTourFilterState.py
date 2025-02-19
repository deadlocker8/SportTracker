from __future__ import annotations

import json

from flask import session

from sporttracker.logic.model.PlannedTour import TravelDirection, TravelType


class PlannedTourFilterState:
    def __init__(self) -> None:
        self._isDoneSelected = True
        self._isTodoSelected = True
        self._arrivalMethods = {travelType: True for travelType in TravelType}
        self._departureMethods = {travelType: True for travelType in TravelType}
        self._directions = {travelDirection: True for travelDirection in TravelDirection}

    def update(
        self,
        isDoneSelected: bool,
        isTodoSelected: bool,
        arrivalMethods: dict[TravelType, bool],
        departureMethods: dict[TravelType, bool],
        directions: dict[TravelDirection, bool],
    ):
        self._isDoneSelected = isDoneSelected
        self._isTodoSelected = isTodoSelected
        self._arrivalMethods = arrivalMethods
        self._departureMethods = departureMethods
        self._directions = directions

    def is_done_selected(self) -> bool:
        return self._isDoneSelected

    def is_todo_selected(self) -> bool:
        return self._isTodoSelected

    def get_selected_arrival_methods(self) -> list[TravelType]:
        selectedItems = [
            travelType for travelType, isActive in self._arrivalMethods.items() if isActive
        ]
        return sorted(selectedItems, key=lambda entry: entry.order)

    def get_selected_departure_methods(self) -> list[TravelType]:
        selectedItems = [
            travelType for travelType, isActive in self._departureMethods.items() if isActive
        ]
        return sorted(selectedItems, key=lambda entry: entry.order)

    def get_selected_directions(self) -> list[TravelDirection]:
        selectedItems = [
            directionType for directionType, isActive in self._directions.items() if isActive
        ]
        return sorted(selectedItems, key=lambda entry: entry.order)

    def to_json(self) -> str:
        return json.dumps(
            {
                'isDoneSelected': self._isDoneSelected,
                'isTodoSelected': self._isTodoSelected,
                'arrivalMethods': {
                    travelType.name: isActive
                    for travelType, isActive in self._arrivalMethods.items()
                },
                'departureMethods': {
                    travelType.name: isActive
                    for travelType, isActive in self._departureMethods.items()
                },
                'directions': {
                    directionType.name: isActive
                    for directionType, isActive in self._directions.items()
                },
            }
        )

    @staticmethod
    def from_json(jsonString: str) -> PlannedTourFilterState:
        jsonData = json.loads(jsonString)

        arrivalMethods = {}
        for travelTypeName, isActive in jsonData['arrivalMethods'].items():
            try:
                travelType = TravelType(travelTypeName)  # type: ignore[call-arg]
                arrivalMethods[travelType] = isActive
            except ValueError:
                pass

        departureMethods = {}
        for travelTypeName, isActive in jsonData['departureMethods'].items():
            try:
                travelType = TravelType(travelTypeName)  # type: ignore[call-arg]
                departureMethods[travelType] = isActive
            except ValueError:
                pass

        directions = {}
        for directionTypeName, isActive in jsonData['directions'].items():
            try:
                directionType = TravelDirection(directionTypeName)  # type: ignore[call-arg]
                directions[directionType] = isActive
            except ValueError:
                pass

        plannedTourFilterState = PlannedTourFilterState()
        plannedTourFilterState.update(
            jsonData['isDoneSelected'],
            jsonData['isTodoSelected'],
            arrivalMethods,
            departureMethods,
            directions,
        )
        return plannedTourFilterState


def get_planned_tour_filter_state_from_session() -> PlannedTourFilterState:
    if 'plannedTourFilterState' not in session:
        session['plannedTourFilterState'] = PlannedTourFilterState().to_json()

    return PlannedTourFilterState.from_json(session['plannedTourFilterState'])
