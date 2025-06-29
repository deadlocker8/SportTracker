from sqlalchemy import String, Boolean, Integer, JSON
from sqlalchemy.orm import mapped_column, Mapped

from sporttracker.logic.model.PlannedTour import TravelType, TravelDirection
from sporttracker.logic.model.db import db


class PlannedTourFilterState(db.Model):  # type: ignore[name-defined]
    __tablename__ = 'filter_state_planned_tour'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, primary_key=True)
    is_done_selected: Mapped[Boolean] = mapped_column(Boolean, nullable=False)
    is_todo_selected: Mapped[Boolean] = mapped_column(Boolean, nullable=False)
    arrival_methods = db.Column(JSON)
    departure_methods = db.Column(JSON)
    directions = db.Column(JSON)
    name_filter: Mapped[String] = mapped_column(String, nullable=True)
    minimum_distance: Mapped[Integer] = mapped_column(Integer, nullable=True)
    maximum_distance: Mapped[Integer] = mapped_column(Integer, nullable=True)
    is_long_distance_tours_include_selected: Mapped[Boolean] = mapped_column(Boolean, nullable=False)
    is_long_distance_tours_exclude_selected: Mapped[Boolean] = mapped_column(Boolean, nullable=False)

    def __repr__(self):
        return (
            f'PlannedTourFilterState('
            f'user_id: {self.user_id}, '
            f'is_done_selected: {self.is_done_selected}, '
            f'is_todo_selected: {self.is_todo_selected}, '
            f'arrival_methods: {self.arrival_methods}, '
            f'departure_methods: {self.departure_methods}, '
            f'directions: {self.directions}, '
            f'name_filter: {self.name_filter}, '
            f'minimum_distance: {self.minimum_distance}, '
            f'maximum_distance: {self.maximum_distance}, '
            f'is_long_distance_tours_include_selected: {self.is_long_distance_tours_include_selected}, '
            f'is_long_distance_tours_exclude_selected: {self.is_long_distance_tours_exclude_selected})'
        )

    def get_selected_arrival_methods(self) -> list[TravelType]:
        return self.__get_selected_travel_types(self.arrival_methods)

    def get_selected_departure_methods(self) -> list[TravelType]:
        return self.__get_selected_travel_types(self.departure_methods)

    @staticmethod
    def __get_selected_travel_types(items: dict[str, bool]) -> list[TravelType]:
        castedItems = {}
        for travelTypeName, isActive in items.items():
            try:
                travelType = TravelType(travelTypeName)  # type: ignore[call-arg]
                castedItems[travelType] = isActive
            except ValueError:
                pass

        selectedItems = [travelType for travelType, isActive in castedItems.items() if isActive]
        return sorted(selectedItems, key=lambda entry: entry.order)

    def get_selected_directions(self) -> list[TravelDirection]:
        directions = {}
        for directionTypeName, isActive in self.directions.items():
            try:
                directionType = TravelDirection(directionTypeName)  # type: ignore[call-arg]
                directions[directionType] = isActive
            except ValueError:
                pass

        selectedItems = [directionType for directionType, isActive in directions.items() if isActive]
        return sorted(selectedItems, key=lambda entry: entry.order)

    def update(
        self,
        is_done_selected: bool,
        is_todo_selected: bool,
        arrival_methods: dict[TravelType, bool],
        departure_methods: dict[TravelType, bool],
        directions: dict[TravelDirection, bool],
        name_filter: str | None,
        minimum_distance: int | None = None,
        maximum_distance: int | None = None,
        is_long_distance_tours_include_selected: bool = True,
        is_long_distance_tours_exclude_selected: bool = True,
    ):
        self.is_done_selected = is_done_selected  # type: ignore[assignment]
        self.is_todo_selected = is_todo_selected  # type: ignore[assignment]
        self.arrival_methods = {enumValue.name: isActive for enumValue, isActive in arrival_methods.items()}
        self.departure_methods = {enumValue.name: isActive for enumValue, isActive in departure_methods.items()}
        self.directions = {enumValue.name: isActive for enumValue, isActive in directions.items()}
        self.name_filter = name_filter  # type: ignore[assignment]
        self.minimum_distance = minimum_distance  # type: ignore[assignment]
        self.maximum_distance = maximum_distance  # type: ignore[assignment]
        self.is_long_distance_tours_include_selected = is_long_distance_tours_include_selected  # type: ignore[assignment]
        self.is_long_distance_tours_exclude_selected = is_long_distance_tours_exclude_selected  # type: ignore[assignment]


def get_planned_tour_filter_state_by_user(user_id: int) -> PlannedTourFilterState:
    return PlannedTourFilterState.query.filter(PlannedTourFilterState.user_id == user_id).first()
