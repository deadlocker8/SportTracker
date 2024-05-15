from __future__ import annotations

import enum
from dataclasses import dataclass


@dataclass
class Achievement:
    icon: str
    is_font_awesome_icon: bool
    color: str
    title: str
    description: str


class AnnualAchievementDifferenceType(enum.Enum):
    LESS = 'LESS', 'trending_down', 'text-danger'
    EQUAL = 'EQUAL', 'trending_up', 'text-success'
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
    difference_type: AnnualAchievementDifferenceType
    all_year_data: AllYearData
    unit: str
