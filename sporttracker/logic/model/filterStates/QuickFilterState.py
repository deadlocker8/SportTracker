from sqlalchemy import JSON

from sporttracker.logic.model.WorkoutType import WorkoutType
from sporttracker.logic.model.db import db


class QuickFilterState(db.Model):  # type: ignore[name-defined]
    __tablename__ = 'filter_state_quick'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, primary_key=True)
    workout_types = db.Column(JSON)
    years = db.Column(JSON)

    def __repr__(self):
        return f'QuickFilterState(user_id: {self.user_id}, workout_types: {self.workout_types}, years: {self.years})'

    def get_active_types(self) -> list[WorkoutType]:
        workoutTypes = {}
        for workoutTypeName, isActive in self.workout_types.items():
            try:
                workoutType = WorkoutType(workoutTypeName)  # type: ignore[call-arg]
                workoutTypes[workoutType] = isActive
            except ValueError:
                pass

        return [workoutType for workoutType, isActive in workoutTypes.items() if isActive]

    def get_active_distance_workout_types(self) -> list[WorkoutType]:
        return [
            workoutType
            for workoutType in self.get_active_types()
            if workoutType in WorkoutType.get_distance_workout_types()
        ]

    def update(
        self,
        workout_types: dict[WorkoutType, bool],
        years: list[int],
    ):
        self.workout_types = {enumValue.name: isActive for enumValue, isActive in workout_types.items()}
        self.years = years

    def reset(self, availableYears: list[int]) -> None:
        self.update({workoutType: True for workoutType in WorkoutType}, availableYears)


def get_quick_filter_state_by_user(user_id: int) -> QuickFilterState:
    return QuickFilterState.query.filter(QuickFilterState.user_id == user_id).first()
