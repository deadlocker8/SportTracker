from abc import abstractmethod, ABC
from dataclasses import dataclass
from datetime import date
from typing import ClassVar

from flask_babel import format_datetime
from flask_login import current_user
from sqlalchemy import Integer
from sqlalchemy.orm import mapped_column, Mapped

from logic.model.Track import TrackType, get_tracks_by_year_and_month_by_type
from logic.model.User import User
from logic.model.db import db


@dataclass
class MonthGoalSummary(ABC):
    id: int
    type: TrackType
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

    goal_count_minimum: float
    goal_count_perfect: float
    actual_count: float

    def get_actual_value_formatted(self) -> str:
        return f'{self.actual_count} / {self.goal_count_perfect}'


class MonthGoal(db.Model):
    __abstract__ = True
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type = db.Column(db.Enum(TrackType))
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
        tracks = get_tracks_by_year_and_month_by_type(self.year, self.month, [self.type])

        actualDistance = 0
        if tracks:
            actualDistance = sum([t.distance for t in tracks])

        color = self.__determine_color(actualDistance)
        name = format_datetime(date(year=self.year, month=self.month, day=1), format='MMMM yyyy')
        percentage = actualDistance / self.distance_perfect * 100
        return MonthGoalDistanceSummary(id=self.id,
                                        type=self.type,
                                        name=name,
                                        goal_distance_minimum=self.distance_minimum / 1000,
                                        goal_distance_perfect=self.distance_perfect / 1000,
                                        actual_distance=actualDistance / 1000,
                                        percentage=percentage,
                                        color=color)

    def __determine_color(self, actualDistance: float) -> str:
        if actualDistance >= self.distance_perfect:
            return 'bg-success'
        elif actualDistance >= self.distance_minimum:
            return 'bg-warning'

        return 'bg-danger'


class MonthGoalCount(MonthGoal):
    count_minimum: Mapped[int] = mapped_column(Integer, nullable=False)
    count_perfect: Mapped[int] = mapped_column(Integer, nullable=False)

    def get_summary(self) -> MonthGoalCountSummary:
        tracks = get_tracks_by_year_and_month_by_type(self.year, self.month, [self.type])

        actualCount = 0
        if tracks:
            actualCount = len(tracks)

        color = self.__determine_color(actualCount)
        name = format_datetime(date(year=self.year, month=self.month, day=1), format='MMMM yyyy')
        percentage = actualCount / self.count_perfect * 100
        return MonthGoalCountSummary(id=self.id,
                                     type=self.type,
                                     name=name,
                                     goal_count_minimum=self.count_minimum,
                                     goal_count_perfect=self.count_perfect,
                                     actual_count=actualCount,
                                     percentage=percentage,
                                     color=color)

    def __determine_color(self, actualCount: float) -> str:
        if actualCount >= self.count_perfect:
            return 'bg-success'
        elif actualCount >= self.count_minimum:
            return 'bg-warning'

        return 'bg-danger'


def get_goal_summaries_by_year_and_month(year: int, month: int) -> list[MonthGoalSummary]:
    goalsDistance = (MonthGoalDistance.query.join(User)
                     .filter(User.username == current_user.username)
                     .filter(MonthGoalDistance.year == year)
                     .filter(MonthGoalDistance.month == month)
                     .all())
    goalsCount = (MonthGoalCount.query.join(User)
                  .filter(User.username == current_user.username)
                  .filter(MonthGoalCount.year == year)
                  .filter(MonthGoalCount.month == month)
                  .all())

    return [goal.get_summary() for goal in goalsDistance + goalsCount]
