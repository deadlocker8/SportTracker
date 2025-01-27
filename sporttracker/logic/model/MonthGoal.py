from abc import abstractmethod, ABC
from dataclasses import dataclass
from datetime import date
from typing import ClassVar

from flask_babel import format_datetime
from flask_login import current_user
from sqlalchemy import Integer
from sqlalchemy.orm import mapped_column, Mapped

from sporttracker.helpers.Helpers import format_duration
from sporttracker.logic.model.Workout import get_workouts_by_year_and_month_by_type
from sporttracker.logic.model.WorkoutType import WorkoutType
from sporttracker.logic.model.User import User
from sporttracker.logic.model.db import db


@dataclass
class MonthGoalSummary(ABC):
    id: int
    type: WorkoutType
    name: str
    percentage: float
    color: str

    @abstractmethod
    def get_actual_value_formatted(self) -> str:
        pass


@dataclass
class MonthGoalDistanceSummary(MonthGoalSummary):
    type_name: ClassVar[str] = 'DISTANCE'
    icon: ClassVar[str] = 'route'
    is_outlined_icon: ClassVar[bool] = True

    goal_distance_minimum: float
    goal_distance_perfect: float
    actual_distance: float

    def get_actual_value_formatted(self) -> str:
        value = str(int(self.actual_distance))

        if len(value) == 1:
            return f'&nbsp;&nbsp;{value} km'
        elif len(value) == 2:
            return f'&nbsp;{value} km'
        else:
            return f'{value} km'


@dataclass
class MonthGoalCountSummary(MonthGoalSummary):
    type_name: ClassVar[str] = 'COUNT'
    icon: ClassVar[str] = 'format_list_numbered'
    is_outlined_icon: ClassVar[bool] = False

    goal_count_minimum: float
    goal_count_perfect: float
    actual_count: float

    def get_actual_value_formatted(self) -> str:
        return f'{self.actual_count} / {self.goal_count_perfect}'


@dataclass
class MonthGoalDurationSummary(MonthGoalSummary):
    type_name: ClassVar[str] = 'DURATION'
    icon: ClassVar[str] = 'timer'
    is_outlined_icon: ClassVar[bool] = True

    goal_duration_minimum: float
    goal_duration_perfect: float
    actual_duration: float

    def get_actual_value_formatted(self) -> str:
        return f'{format_duration(int(self.actual_duration))} h'


class MonthGoal(db.Model):  # type: ignore[name-defined]
    __abstract__ = True
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type = db.Column(db.Enum(WorkoutType))
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    @abstractmethod
    def get_summary(self) -> MonthGoalSummary:
        pass


class MonthGoalDistance(MonthGoal):
    distance_minimum: Mapped[int] = mapped_column(Integer, nullable=False)
    distance_perfect: Mapped[int] = mapped_column(Integer, nullable=False)

    def get_summary(self) -> MonthGoalDistanceSummary:
        workouts = get_workouts_by_year_and_month_by_type(self.year, self.month, [self.type])

        actualDistance = 0
        if workouts:
            actualDistance = sum([t.distance for t in workouts])

        color = self.__determine_color(actualDistance)
        name = format_datetime(date(year=self.year, month=self.month, day=1), format='MMMM yyyy')
        percentage = actualDistance / self.distance_perfect * 100
        return MonthGoalDistanceSummary(
            id=self.id,
            type=self.type,
            name=name,
            goal_distance_minimum=self.distance_minimum / 1000,
            goal_distance_perfect=self.distance_perfect / 1000,
            actual_distance=actualDistance / 1000,
            percentage=percentage,
            color=color,
        )

    def __determine_color(self, actualDistance: float) -> str:
        if actualDistance >= self.distance_perfect:
            return 'bg-success'
        elif actualDistance >= self.distance_minimum:
            return 'bg-warning'

        return 'bg-danger'

    def __repr__(self):
        return (
            f'MonthGoalDistance('
            f'id: {self.id}, '
            f'type: {self.type}, '
            f'year: {self.year}, '
            f'month: {self.month}, '
            f'distance_minimum: {self.distance_minimum}, '
            f'distance_perfect: {self.distance_perfect}, '
            f'user_id: {self.user_id})'
        )


class MonthGoalCount(MonthGoal):
    count_minimum: Mapped[int] = mapped_column(Integer, nullable=False)
    count_perfect: Mapped[int] = mapped_column(Integer, nullable=False)

    def get_summary(self) -> MonthGoalCountSummary:
        workouts = get_workouts_by_year_and_month_by_type(self.year, self.month, [self.type])

        actualCount = 0
        if workouts:
            actualCount = len(workouts)

        color = self.__determine_color(actualCount)
        name = format_datetime(date(year=self.year, month=self.month, day=1), format='MMMM yyyy')
        percentage = actualCount / self.count_perfect * 100
        return MonthGoalCountSummary(
            id=self.id,
            type=self.type,
            name=name,
            goal_count_minimum=self.count_minimum,
            goal_count_perfect=self.count_perfect,
            actual_count=actualCount,
            percentage=percentage,
            color=color,
        )

    def __determine_color(self, actualCount: float) -> str:
        if actualCount >= self.count_perfect:
            return 'bg-success'
        elif actualCount >= self.count_minimum:
            return 'bg-warning'

        return 'bg-danger'

    def __repr__(self):
        return (
            f'MonthGoalDistance('
            f'id: {self.id}, '
            f'type: {self.type}, '
            f'year: {self.year}, '
            f'month: {self.month}, '
            f'count_minimum: {self.count_minimum}, '
            f'count_perfect: {self.count_perfect}, '
            f'user_id: {self.user_id})'
        )


class MonthGoalDuration(MonthGoal):
    duration_minimum: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_perfect: Mapped[int] = mapped_column(Integer, nullable=False)

    def get_summary(self) -> MonthGoalDurationSummary:
        try:
            workouts = get_workouts_by_year_and_month_by_type(self.year, self.month, [self.type])
        except ValueError:
            workouts = []

        actualDuration = 0
        if workouts:
            actualDuration = sum([t.duration for t in workouts])

        color = self.__determine_color(actualDuration)
        name = format_datetime(date(year=self.year, month=self.month, day=1), format='MMMM yyyy')
        percentage = actualDuration / self.duration_perfect * 100
        return MonthGoalDurationSummary(
            id=self.id,
            type=self.type,
            name=name,
            goal_duration_minimum=self.duration_minimum,
            goal_duration_perfect=self.duration_perfect,
            actual_duration=actualDuration,
            percentage=percentage,
            color=color,
        )

    def __determine_color(self, actualDuration: int) -> str:
        if actualDuration >= self.duration_perfect:
            return 'bg-success'
        elif actualDuration >= self.duration_minimum:
            return 'bg-warning'

        return 'bg-danger'

    def __repr__(self):
        return (
            f'MonthGoalDuration('
            f'id: {self.id}, '
            f'type: {self.type}, '
            f'year: {self.year}, '
            f'month: {self.month}, '
            f'duration_minimum: {self.duration_minimum}, '
            f'duration_perfect: {self.duration_perfect}, '
            f'user_id: {self.user_id})'
        )


def get_goal_summaries_by_year_and_month_and_types(
    year: int, month: int, workoutTypes: list[WorkoutType]
) -> list[MonthGoalSummary]:
    goalsDistance = (
        MonthGoalDistance.query.join(User)
        .filter(User.username == current_user.username)
        .filter(MonthGoalDistance.year == year)
        .filter(MonthGoalDistance.month == month)
        .filter(MonthGoalDistance.type.in_(workoutTypes))
        .all()
    )
    goalsCount = (
        MonthGoalCount.query.join(User)
        .filter(User.username == current_user.username)
        .filter(MonthGoalCount.year == year)
        .filter(MonthGoalCount.month == month)
        .filter(MonthGoalCount.type.in_(workoutTypes))
        .all()
    )
    goalsDuration = (
        MonthGoalDuration.query.join(User)
        .filter(User.username == current_user.username)
        .filter(MonthGoalDuration.year == year)
        .filter(MonthGoalDuration.month == month)
        .filter(MonthGoalDuration.type.in_(workoutTypes))
        .all()
    )

    return [goal.get_summary() for goal in goalsDistance + goalsCount + goalsDuration]


def get_month_goal_count_by_id(goal_id: int) -> MonthGoalCount | None:
    return (
        MonthGoalCount.query.join(User)
        .filter(User.username == current_user.username)
        .filter(MonthGoalCount.id == goal_id)
        .first()
    )


def get_month_goal_distance_by_id(goal_id: int) -> MonthGoalDistance | None:
    return (
        MonthGoalDistance.query.join(User)
        .filter(User.username == current_user.username)
        .filter(MonthGoalDistance.id == goal_id)
        .first()
    )


def get_month_goal_duration_by_id(goal_id: int) -> MonthGoalDuration | None:
    return (
        MonthGoalDuration.query.join(User)
        .filter(User.username == current_user.username)
        .filter(MonthGoalDuration.id == goal_id)
        .first()
    )
