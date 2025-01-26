from flask_login import current_user
from sporttracker.logic.model.FitnessWorkoutType import FitnessWorkoutType
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, Mapped

from sporttracker.logic.model.Sport import Sport
from sporttracker.logic.model.FitnessWorkoutCategory import FitnessWorkoutCategory
from sporttracker.logic.model.db import db


class WorkoutSport(Sport):  # type: ignore[name-defined]
    __tablename__ = 'workout_sport'
    id: Mapped[int] = mapped_column(ForeignKey('sport.id'), primary_key=True)
    workout_type = db.Column(db.Enum(FitnessWorkoutType), nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': 'workout_sport',
    }

    def __repr__(self):
        return (
            f'WorkoutSport('
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
                FitnessWorkoutCategory.sport_id == self.id
            ).all()
        ]


def get_workout_sport_by_id(distance_sport_id: int) -> WorkoutSport | None:
    return (
        WorkoutSport.query.filter(WorkoutSport.user_id == current_user.id)
        .filter(WorkoutSport.id == distance_sport_id)
        .first()
    )
