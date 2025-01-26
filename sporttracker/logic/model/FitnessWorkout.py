from flask_login import current_user
from sporttracker.logic.model.FitnessWorkoutType import FitnessWorkoutType
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, Mapped

from sporttracker.logic.model.Workout import Workout
from sporttracker.logic.model.FitnessWorkoutCategory import FitnessWorkoutCategory
from sporttracker.logic.model.db import db


class FitnessWorkout(Workout):  # type: ignore[name-defined]
    __tablename__ = 'fitness_workout'
    id: Mapped[int] = mapped_column(ForeignKey('workout.id'), primary_key=True)
    workout_type = db.Column(db.Enum(FitnessWorkoutType), nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': 'fitness_workout',
    }

    def __repr__(self):
        return (
            f'FitnessWorkout('
            f'name: {self.name}, '
            f'start_time: {self.start_time}, '
            f'duration: {self.duration}, '
            f'custom_fields: {self.custom_fields}, '
            f'participants: {self.participants}, '
            f'user_id: {self.user_id})'
            f'workout_type: {self.workout_type})'
        )

    def get_workout_categories(self) -> list[str]:
        return [
            c.workout_category_type
            for c in FitnessWorkoutCategory.query.filter(
                FitnessWorkoutCategory.workout_id == self.id
            ).all()
        ]


def get_fitness_workout_by_id(distance_workout_id: int) -> FitnessWorkout | None:
    return (
        FitnessWorkout.query.filter(FitnessWorkout.user_id == current_user.id)
        .filter(FitnessWorkout.id == distance_workout_id)
        .first()
    )
