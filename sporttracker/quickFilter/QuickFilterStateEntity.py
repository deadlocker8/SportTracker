from __future__ import annotations
from sqlalchemy import JSON
from sqlalchemy.ext.mutable import MutableDict

from sporttracker.workout.WorkoutService import WorkoutService
from sporttracker.workout.WorkoutType import WorkoutType
from sporttracker.db import db


class QuickFilterState(db.Model):  # type: ignore[name-defined]
    __tablename__ = 'filter_state_quick'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, primary_key=True)
    workout_types = db.Column(MutableDict.as_mutable(JSON))  # type: ignore[arg-type]
    years = db.Column(MutableDict.as_mutable(JSON))  # type: ignore[arg-type]

    def __repr__(self):
        return f'QuickFilterState(user_id: {self.user_id}, workout_types: {self.workout_types}, years: {self.years})'

    def get_workout_types(self) -> dict[WorkoutType, bool]:
        workoutTypes = {}
        for workoutTypeName, isActive in self.workout_types.items():
            try:
                workoutType = WorkoutType(workoutTypeName)  # type: ignore[call-arg]
                workoutTypes[workoutType] = isActive
            except ValueError:
                pass

        return workoutTypes

    def get_active_workout_types(self) -> list[WorkoutType]:
        return [workoutType for workoutType, isActive in self.get_workout_types().items() if isActive]

    def get_active_distance_workout_types(self) -> list[WorkoutType]:
        return [
            workoutType
            for workoutType in self.get_active_workout_types()
            if workoutType in WorkoutType.get_distance_workout_types()
        ]

    def get_years(self) -> dict[int, bool]:
        return {int(year): isActive for year, isActive in self.years.items()}

    def get_active_years(self) -> list[int]:
        return sorted([int(year) for year, isActive in self.get_years().items() if isActive])

    def is_all_years_active(self) -> bool:
        return all(self.years.values())

    def update(
        self,
        workout_types: dict[WorkoutType, bool],
        active_years: list[int],
    ):
        self.workout_types = {enumValue.name: isActive for enumValue, isActive in workout_types.items()}

        if self.years is None:
            self.years = {year: True for year in active_years}

        for year in self.years:
            self.years[year] = int(year) in active_years

    def reset(self, available_years: list[int]) -> QuickFilterState:
        self.update({workoutType: True for workoutType in WorkoutType}, available_years)
        return self

    def toggle_workout_type(self, workoutType: WorkoutType) -> None:
        self.workout_types[workoutType.name] = not self.workout_types[workoutType.name]

    def enable_all_workout_types(self) -> None:
        self.update({workoutType: True for workoutType in WorkoutType}, self.get_active_years())

    def update_missing_values(self, available_years: list[int]) -> bool:
        filterWorkoutTypes = self.get_workout_types()

        isUpdated = False
        for workoutType in [t for t in WorkoutType]:
            if workoutType not in filterWorkoutTypes:
                self.workout_types[workoutType.name] = True
                isUpdated = True

        for year in available_years:
            if year not in self.get_years():
                self.years[year] = True
                isUpdated = True

        return isUpdated


def get_quick_filter_state_by_user(user_id: int) -> QuickFilterState:
    quickFilterState = QuickFilterState.query.filter(QuickFilterState.user_id == user_id).first()
    if quickFilterState.update_missing_values(WorkoutService.get_available_years(user_id)):
        db.session.commit()

    return quickFilterState
