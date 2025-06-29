from __future__ import annotations

import json

from flask import session

from sporttracker.logic.model.PlannedTour import TravelDirection
from sporttracker.logic.model.TravelType import TravelType


class PlannedTourFilterState:
    def __init__(self) -> None:
        self._isDoneSelected = True
        self._isTodoSelected = True
        self._arrivalMethods = {travelType: True for travelType in TravelType}
        self._departureMethods = {travelType: True for travelType in TravelType}
        self._directions = {travelDirection: True for travelDirection in TravelDirection}
        self._name_filter: str | None = None
        self._minimum_distance: int | None = None
        self._maximum_distance: int | None = None
        self._isLongDistanceToursIncludeSelected: bool = True
        self._isLongDistanceToursExcludeSelected: bool = True

    def update(
        self,
        isDoneSelected: bool,
        isTodoSelected: bool,
        arrivalMethods: dict[TravelType, bool],
        departureMethods: dict[TravelType, bool],
        directions: dict[TravelDirection, bool],
        nameFilter: str | None,
        minimum_distance: int | None = None,
        maximum_distance: int | None = None,
        isLongDistanceToursIncludeSelected: bool = True,
        isLongDistanceToursExcludeSelected: bool = True,
    ):
        self._isDoneSelected = isDoneSelected
        self._isTodoSelected = isTodoSelected
        self._arrivalMethods = arrivalMethods
        self._departureMethods = departureMethods
        self._directions = directions
        self._name_filter = nameFilter
        self._minimum_distance = minimum_distance
        self._maximum_distance = maximum_distance
        self._isLongDistanceToursIncludeSelected = isLongDistanceToursIncludeSelected
        self._isLongDistanceToursExcludeSelected = isLongDistanceToursExcludeSelected

    def is_done_selected(self) -> bool:
        return self._isDoneSelected

    def is_todo_selected(self) -> bool:
        return self._isTodoSelected

    def get_selected_arrival_methods(self) -> list[TravelType]:
        selectedItems = [travelType for travelType, isActive in self._arrivalMethods.items() if isActive]
        return sorted(selectedItems, key=lambda entry: entry.order)

    def get_selected_departure_methods(self) -> list[TravelType]:
        selectedItems = [travelType for travelType, isActive in self._departureMethods.items() if isActive]
        return sorted(selectedItems, key=lambda entry: entry.order)

    def get_selected_directions(self) -> list[TravelDirection]:
        selectedItems = [directionType for directionType, isActive in self._directions.items() if isActive]
        return sorted(selectedItems, key=lambda entry: entry.order)

    def get_name_filter(self) -> str | None:
        return self._name_filter

    def get_minimum_distance(self) -> int | None:
        return self._minimum_distance

    def get_maximum_distance(self) -> int | None:
        return self._maximum_distance

    def is_long_distance_tours_include_selected(self) -> bool:
        return self._isLongDistanceToursIncludeSelected

    def is_long_distance_tours_exclude_selected(self) -> bool:
        return self._isLongDistanceToursExcludeSelected

    def to_json(self) -> str:
        return json.dumps(
            {
                'isDoneSelected': self._isDoneSelected,
                'isTodoSelected': self._isTodoSelected,
                'arrivalMethods': {travelType.name: isActive for travelType, isActive in self._arrivalMethods.items()},
                'departureMethods': {
                    travelType.name: isActive for travelType, isActive in self._departureMethods.items()
                },
                'directions': {directionType.name: isActive for directionType, isActive in self._directions.items()},
                'nameFilter': self._name_filter,
                'minimum_distance': self._minimum_distance,
                'maximum_distance': self._maximum_distance,
                'isLongDistanceToursIncludeSelected': self._isLongDistanceToursIncludeSelected,
                'isLongDistanceToursExcludeSelected': self._isLongDistanceToursExcludeSelected,
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
            jsonData['nameFilter'],
            jsonData['minimum_distance'],
            jsonData['maximum_distance'],
            jsonData['isLongDistanceToursIncludeSelected']
            if 'isLongDistanceToursIncludeSelected' in jsonData
            else True,
            jsonData['isLongDistanceToursExcludeSelected']
            if 'isLongDistanceToursExcludeSelected' in jsonData
            else True,
        )
        return plannedTourFilterState


def get_planned_tour_filter_state_from_session() -> PlannedTourFilterState:
    if 'plannedTourFilterState' not in session:
        session['plannedTourFilterState'] = PlannedTourFilterState().to_json()

    return PlannedTourFilterState.from_json(session['plannedTourFilterState'])
