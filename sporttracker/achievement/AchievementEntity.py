from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, date
from typing import Sequence

from flask import url_for
from flask_babel import gettext, format_datetime

from sporttracker.helpers import Helpers
from sporttracker.workout.WorkoutType import WorkoutType


@dataclass
class AchievementHistoryItem(ABC):
    date: datetime | date | None

    @abstractmethod
    def get_date_formatted(self) -> str:
        pass

    @abstractmethod
    def get_value_formatted(self) -> str:
        pass

    @abstractmethod
    def get_link(self) -> str | None:
        pass


@dataclass
class DistanceAchievementHistoryItem(AchievementHistoryItem, ABC):
    value: float

    def get_value_formatted(self) -> str:
        return f'{Helpers.format_decimal(self.value, decimals=2)} km'


@dataclass
class BestMonthDistanceAchievementHistoryItem(DistanceAchievementHistoryItem):
    def get_date_formatted(self) -> str:
        if self.date is None:
            return gettext('No month')

        return format_datetime(self.date, format='MMMM yyyy')

    def get_link(self) -> str | None:
        if self.date is None:
            return None

        return f'<a href="{url_for("workouts.listWorkouts", year=self.date.year, month=self.date.month)}">{self.get_date_formatted()}</a>'

    @staticmethod
    def get_dummy_instance() -> BestMonthDistanceAchievementHistoryItem:
        return BestMonthDistanceAchievementHistoryItem(None, 0.0)


@dataclass
class LongestWorkoutDistanceAchievementHistoryItem(DistanceAchievementHistoryItem):
    workout_id: int | None

    def get_date_formatted(self) -> str:
        if self.date is None:
            return gettext('no date')

        return format_datetime(self.date, format='dd.MM.yyyy')

    def get_link(self) -> str | None:
        if self.workout_id is None:
            return None

        return (
            f'<a href="{url_for("maps.showSingleWorkout", workout_id=self.workout_id)}">{self.get_date_formatted()}</a>'
        )

    @staticmethod
    def get_dummy_instance() -> LongestWorkoutDistanceAchievementHistoryItem:
        return LongestWorkoutDistanceAchievementHistoryItem(None, 0.0, None)


@dataclass
class DurationAchievementHistoryItem(AchievementHistoryItem, ABC):
    value: int

    def get_value_formatted(self) -> str:
        return f'{Helpers.format_duration(self.value)} h'


@dataclass
class BestMonthDurationAchievementHistoryItem(DurationAchievementHistoryItem):
    def get_date_formatted(self) -> str:
        if self.date is None:
            return gettext('No month')

        return format_datetime(self.date, format='MMMM yyyy')

    def get_link(self) -> str | None:
        if self.date is None:
            return None

        return f'<a href="{url_for("workouts.listWorkouts", year=self.date.year, month=self.date.month)}">{self.get_date_formatted()}</a>'

    @staticmethod
    def get_dummy_instance() -> BestMonthDurationAchievementHistoryItem:
        return BestMonthDurationAchievementHistoryItem(None, 0)


@dataclass
class LongestWorkoutDurationAchievementHistoryItem(DurationAchievementHistoryItem):
    workout_id: int | None
    workout_type: WorkoutType | None

    def get_date_formatted(self) -> str:
        if self.date is None:
            return gettext('no date')

        return format_datetime(self.date, format='dd.MM.yyyy')

    def get_link(self) -> str | None:
        if self.workout_id is None:
            return None

        if self.workout_type == WorkoutType.FITNESS:
            return f'<a href="{url_for("fitnessWorkouts.edit", workout_id=self.workout_id)}">{self.get_date_formatted()}</a>'
        else:
            return f'<a href="{url_for("distanceWorkouts.edit", workout_id=self.workout_id)}">{self.get_date_formatted()}</a>'

    @staticmethod
    def get_dummy_instance() -> LongestWorkoutDurationAchievementHistoryItem:
        return LongestWorkoutDurationAchievementHistoryItem(None, 0, None, None)


@dataclass
class Achievement:
    icon: str
    is_font_awesome_icon: bool
    is_outlined_icon: bool
    color: str
    title: str
    description: str
    historyItems: Sequence[AchievementHistoryItem]


class AnnualAchievementDifferenceType(enum.Enum):
    LESS = 'LESS', 'trending_down', 'text-danger'
    EQUAL = 'EQUAL', 'trending_flat', 'text-orange'
    MORE = 'MORE', 'trending_up', 'text-success'

    icon: str
    color: str

    def __new__(
        cls,
        name: str,
        icon: str,
        color: str,
    ):
        member = object.__new__(cls)
        member._value_ = name
        member.icon = icon
        member.color = color
        return member

    @staticmethod
    def get_by_difference(difference: float) -> AnnualAchievementDifferenceType:
        if difference < 0:
            return AnnualAchievementDifferenceType.LESS

        if difference == 0:
            return AnnualAchievementDifferenceType.EQUAL

        return AnnualAchievementDifferenceType.MORE


@dataclass
class AllYearData:
    year_names: list[str]
    values: list
    labels: list[str]
    min: str
    max: str
    sum: str
    average: str


@dataclass
class AnnualAchievement(Achievement):
    difference_to_previous_year: str
    difference_percentage: str
    difference_type: AnnualAchievementDifferenceType
    all_year_data: AllYearData
    unit: str
