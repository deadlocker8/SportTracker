from dataclasses import dataclass

from flask_login import current_user
from sqlalchemy import Integer, String, DateTime, extract, func, asc
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import mapped_column, Mapped, relationship

from sporttracker.user.ParticipantEntity import Participant, workout_participant_association
from sporttracker.workout.WorkoutType import WorkoutType
from sporttracker.user.UserEntity import User
from sporttracker.db import db


class Workout(db.Model):  # type: ignore[name-defined]
    __tablename__ = 'workout'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type = db.Column(db.Enum(WorkoutType))
    class_type = db.Column(db.String)
    name: Mapped[String] = mapped_column(String, nullable=False)
    start_time: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    average_heart_rate: Mapped[int] = mapped_column(Integer, nullable=True)
    participants: Mapped[list[Participant]] = relationship(secondary=workout_participant_association)
    custom_fields = db.Column(JSON)

    __mapper_args__ = {
        'polymorphic_identity': 'workout',
        'polymorphic_on': 'class_type',
    }

    def __repr__(self):
        return (
            f'Workout('
            f'id: {self.id}, '
            f'type: {self.type}, '
            f'name: {self.name}, '
            f'start_time: {self.start_time}, '
            f'duration: {self.duration}, '
            f'custom_fields: {self.custom_fields}, '
            f'participants: {self.participants}, '
            f'user_id: {self.user_id}, '
            f'average_heart_rate: {self.average_heart_rate})'
        )


@dataclass
class MonthDurationSum:
    year: int
    month: int
    durationSum: int


def get_workouts_by_year_and_month(
    year: int,
    month: int,
) -> list[Workout]:
    return (
        Workout.query.join(User)
        .filter(User.username == current_user.username)
        .filter(extract('year', Workout.start_time) == year)
        .filter(extract('month', Workout.start_time) == month)
        .order_by(Workout.start_time.desc())
        .all()
    )


def get_duration_per_month_by_type(workoutType: WorkoutType, minYear: int, maxYear: int) -> list[MonthDurationSum]:
    year = extract('year', Workout.start_time)
    month = extract('month', Workout.start_time)

    rows = (
        Workout.query.with_entities(
            func.sum(Workout.duration).label('durationSum'),
            year.label('year'),
            month.label('month'),
        )
        .filter(Workout.type == workoutType)
        .filter(Workout.user_id == current_user.id)
        .group_by(year, month)
        .order_by(year, month)
        .all()
    )

    result = []
    for currentYear in range(minYear, maxYear + 1):
        for currentMonth in range(1, 13):
            for row in rows:
                if row.year == currentYear and row.month == currentMonth:
                    result.append(
                        MonthDurationSum(year=currentYear, month=currentMonth, durationSum=int(row.durationSum))
                    )
                    break
            else:
                result.append(MonthDurationSum(year=currentYear, month=currentMonth, durationSum=0))

    return result


def get_workout_names_by_type(workoutType: WorkoutType) -> list[str]:
    rows = (
        Workout.query.with_entities(Workout.name)
        .filter(Workout.user_id == current_user.id)
        .filter(Workout.type == workoutType)
        .group_by(Workout.name)
        .order_by(asc(func.lower(Workout.name)))
        .all()
    )

    return [row[0] for row in rows]


def get_workouts_by_year_and_month_by_type(year: int, month: int, workoutTypes: list[WorkoutType]) -> list[Workout]:
    return (
        Workout.query.join(User)
        .filter(Workout.type.in_(workoutTypes))
        .filter(User.username == current_user.username)
        .filter(extract('year', Workout.start_time) == year)
        .filter(extract('month', Workout.start_time) == month)
        .order_by(Workout.start_time.desc())
        .all()
    )
