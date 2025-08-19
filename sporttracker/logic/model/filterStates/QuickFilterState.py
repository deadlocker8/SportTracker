from __future__ import annotations
from sqlalchemy import JSON
from sqlalchemy.ext.mutable import MutableDict

from sporttracker.workout.WorkoutType import WorkoutType
from sporttracker.logic.model.db import db


class QuickFilterState(db.Model):  # type: ignore[name-defined]
    __tablename__ = 'filter_state_quick'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, primary_key=True)
    workout_types = db.Column(MutableDict.as_mutable(JSON))  # type: ignore[arg-type]
    years = db.Column(JSON)

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

    def update(
        self,
        workout_types: dict[WorkoutType, bool],
        years: list[int],
    ):
        self.workout_types = {enumValue.name: isActive for enumValue, isActive in workout_types.items()}
        self.years = years

    def reset(self, availableYears: list[int]) -> QuickFilterState:
        self.update({workoutType: True for workoutType in WorkoutType}, availableYears)
        return self

    def toggle_workout_type(self, workoutType: WorkoutType) -> None:
        self.workout_types[workoutType.name] = not self.workout_types[workoutType.name]

    def disable_all_workout_types(self) -> None:
        self.update({workoutType: False for workoutType in WorkoutType}, self.years)

    def update_missing_values(self) -> bool:
        filterWorkoutTypes = self.get_workout_types()

        isUpdated = False
        for workoutType in [t for t in WorkoutType]:
            if workoutType not in filterWorkoutTypes:
                self.workout_types[workoutType.name] = True
                isUpdated = True

        return isUpdated


def get_quick_filter_state_by_user(user_id: int) -> QuickFilterState:
    quickFilterState = QuickFilterState.query.filter(QuickFilterState.user_id == user_id).first()
    if quickFilterState.update_missing_values():
        db.session.commit()

    return quickFilterState
