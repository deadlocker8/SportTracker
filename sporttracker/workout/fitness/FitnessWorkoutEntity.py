from sporttracker.workout.fitness.FitnessWorkoutType import FitnessWorkoutType
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, Mapped

from sporttracker.workout.WorkoutEntity import Workout
from sporttracker.workout.fitness.FitnessWorkoutCategory import (
    FitnessWorkoutCategory,
    FitnessWorkoutCategoryType,
)
from sporttracker.db import db


class FitnessWorkout(Workout):  # type: ignore[name-defined]
    __tablename__ = 'fitness_workout'
    id: Mapped[int] = mapped_column(ForeignKey('workout.id'), primary_key=True)
    fitness_workout_type = db.Column(db.Enum(FitnessWorkoutType), nullable=False)

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
            f'user_id: {self.user_id}, '
            f'average_heart_rate: {self.average_heart_rate}, '
            f'fitness_workout_type: {self.fitness_workout_type})'
        )

    def get_workout_categories(self) -> list[FitnessWorkoutCategoryType]:
        return [
            c.fitness_workout_category_type
            for c in FitnessWorkoutCategory.query.filter(FitnessWorkoutCategory.workout_id == self.id).all()
        ]
