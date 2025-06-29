from sporttracker.logic.model.TravelDirection import TravelDirection
from sporttracker.logic.model.TravelType import TravelType
from sporttracker.logic.model.filterStates.PlannedTourFilterState import PlannedTourFilterState


class TestPlannedTourFilterState:
    def test_reset(self) -> None:
        plannedTourFilterState = PlannedTourFilterState()
        plannedTourFilterState.update(
            False,
            False,
            {t: False for t in TravelType},
            {t: False for t in TravelType},
            {d: False for d in TravelDirection},
            'Test',
            16,
            32,
            False,
            False,
        )

        plannedTourFilterState.reset()

        assert plannedTourFilterState.is_done_selected is True
        assert plannedTourFilterState.is_todo_selected is True
        assert plannedTourFilterState.arrival_methods == {t.name: True for t in TravelType}
        assert plannedTourFilterState.departure_methods == {t.name: True for t in TravelType}
        assert plannedTourFilterState.directions == {d.name: True for d in TravelDirection}
        assert plannedTourFilterState.name_filter is None
        assert plannedTourFilterState.minimum_distance is None
        assert plannedTourFilterState.maximum_distance is None
        assert plannedTourFilterState.is_long_distance_tours_include_selected is True
        assert plannedTourFilterState.is_long_distance_tours_exclude_selected is True

    def test_get_selected_arrival_methods(self) -> None:
        plannedTourFilterState = PlannedTourFilterState()
        plannedTourFilterState.arrival_methods = {
            TravelType.NONE.name: False,
            TravelType.TRAIN.name: True,
            TravelType.CAR.name: False,
        }
        assert plannedTourFilterState.get_selected_arrival_methods() == [TravelType.TRAIN]

    def test_get_selected_departure_methods(self) -> None:
        plannedTourFilterState = PlannedTourFilterState()
        plannedTourFilterState.departure_methods = {
            TravelType.NONE.name: False,
            TravelType.TRAIN.name: False,
            TravelType.CAR.name: True,
        }
        assert plannedTourFilterState.get_selected_departure_methods() == [TravelType.CAR]

    def test_get_selected_directions(self) -> None:
        plannedTourFilterState = PlannedTourFilterState()
        plannedTourFilterState.directions = {
            TravelDirection.RETURN.name: False,
            TravelDirection.SINGLE.name: True,
            TravelDirection.ROUNDTRIP.name: False,
        }
        assert plannedTourFilterState.get_selected_directions() == [TravelDirection.SINGLE]

    def test_update_missing_values(self) -> None:
        plannedTourFilterState = PlannedTourFilterState()
        plannedTourFilterState.arrival_methods = {}
        plannedTourFilterState.departure_methods = {}
        plannedTourFilterState.directions = {}
        assert len(plannedTourFilterState.arrival_methods) == 0
        assert len(plannedTourFilterState.departure_methods) == 0
        assert len(plannedTourFilterState.directions) == 0

        plannedTourFilterState.update_missing_values()
        assert plannedTourFilterState.arrival_methods == {
            TravelType.NONE.name: True,
            TravelType.CAR.name: True,
            TravelType.TRAIN.name: True,
        }
        assert plannedTourFilterState.departure_methods == {
            TravelType.NONE.name: True,
            TravelType.CAR.name: True,
            TravelType.TRAIN.name: True,
        }
        assert plannedTourFilterState.directions == {
            TravelDirection.SINGLE.name: True,
            TravelDirection.RETURN.name: True,
            TravelDirection.ROUNDTRIP.name: True,
        }
