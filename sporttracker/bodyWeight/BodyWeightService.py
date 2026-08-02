from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime

from flask_babel import gettext
from sqlalchemy import func

from sporttracker.bodyWeight.BodyWeightEntity import BodyWeight
from sporttracker.db import db
from sporttracker.helpers.Helpers import format_decimal


@dataclass
class BodyWeightEntryModel:
    id: int
    entry_datetime: datetime
    weight: int  # grams
    difference: int | None  # grams vs. previous entry, None for first entry
    difference_formatted: str | None
    difference_type: WeightDifferenceType


class WeightDifferenceType(enum.Enum):
    LESS = 'LESS', 'trending_down', 'text-green'
    EQUAL = 'EQUAL', 'trending_flat', 'text-orange'
    MORE = 'MORE', 'trending_up', 'text-danger'

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
    def get_by_difference(difference: float | int | None) -> WeightDifferenceType:
        if difference is None:
            return WeightDifferenceType.EQUAL

        if difference < 0:
            return WeightDifferenceType.LESS

        if difference == 0:
            return WeightDifferenceType.EQUAL

        return WeightDifferenceType.MORE


class BmiCategory(enum.Enum):
    SEVERE_THINNESS = 'SEVERE_THINNESS', 0, 16.0, '#4b6cb7'
    MODERATE_THINNESS = 'MODERATE_THINNESS', 16.0, 17.0, '#6f8fd0'
    MILD_THINNESS = 'MILD_THINNESS', 17.0, 18.5, '#93aee2'
    NORMAL = 'NORMAL', 18.5, 25.0, '#2ecc71'
    PRE_OBESE = 'PRE_OBESE', 25.0, 30.0, '#f1c40f'
    OBESE_CLASS_I = 'OBESE_CLASS_I', 30.0, 35.0, '#e67e22'
    OBESE_CLASS_II = 'OBESE_CLASS_II', 35.0, 40.0, '#e74c3c'
    OBESE_CLASS_III = 'OBESE_CLASS_III', 40.0, None, '#8e2a2a'

    min_bmi: float
    max_bmi: float | None  # None means open-ended
    color: str

    def __new__(
        cls,
        name: str,
        min_bmi: float,
        max_bmi: float | None,
        color: str,
    ):
        member = object.__new__(cls)
        member._value_ = name
        member.min_bmi = min_bmi
        member.max_bmi = max_bmi
        member.color = color
        return member

    def get_localized_name(self) -> str:
        name = None

        if self == self.SEVERE_THINNESS:
            name = gettext('Severe thinness')
        elif self == self.MODERATE_THINNESS:
            name = gettext('Moderate thinness')
        elif self == self.MILD_THINNESS:
            name = gettext('Mild thinness')
        elif self == self.NORMAL:
            name = gettext('Normal range')
        elif self == self.PRE_OBESE:
            name = gettext('Overweight (pre-obese)')
        elif self == self.OBESE_CLASS_I:
            name = gettext('Obese Class I')
        elif self == self.OBESE_CLASS_II:
            name = gettext('Obese Class II')
        elif self == self.OBESE_CLASS_III:
            name = gettext('Obese Class III')

        if name is not None:
            return f'{name} {self.min_bmi} - {"∞" if self.max_bmi is None else self.max_bmi}'

        raise ValueError(f'Could not get localized name for unsupported BmiCategory: {self}')

    @staticmethod
    def get_bmi_category(bmi: float) -> BmiCategory:
        for category in BmiCategory:
            if category.max_bmi is None or bmi < category.max_bmi:
                return category

        return BmiCategory.OBESE_CLASS_III


class BodyWeightService:
    BMI_SCALE_MAX = 45.0

    @staticmethod
    def calculate_bmi(weight: int | None, height: int | None) -> float | None:
        if weight is None or height is None or height <= 0:
            return None

        height_in_meters = height / 100.0
        return (weight / 1000.0) / (height_in_meters * height_in_meters)

    @staticmethod
    def get_body_weight_entry_by_id(entry_id: int, user_id: int) -> BodyWeight | None:
        return BodyWeight.query.filter(BodyWeight.user_id == user_id).filter(BodyWeight.id == entry_id).first()

    @staticmethod
    def get_entries_ascending(user_id: int) -> list[BodyWeight]:
        return (
            BodyWeight.query.filter(BodyWeight.user_id == user_id)
            .order_by(BodyWeight.datetime.asc(), BodyWeight.id.asc())
            .all()
        )

    @staticmethod
    def get_average_and_min_and_max(user_id: int) -> tuple[int | None, int | None, int | None]:
        result = (
            db.session.query(func.avg(BodyWeight.weight), func.min(BodyWeight.weight), func.max(BodyWeight.weight))
            .filter(BodyWeight.user_id == user_id)
            .first()
        )

        if result is None:
            return None, None, None

        return result

    @staticmethod
    def get_entries_with_difference(user_id: int) -> list[BodyWeightEntryModel]:
        entries = BodyWeightService.get_entries_ascending(user_id)

        models: list[BodyWeightEntryModel] = []
        previousWeight: int | None = None
        for entry in entries:
            difference = None
            if previousWeight is not None:
                difference = entry.weight - previousWeight

            if difference is None:
                differenceFormatted = ''
            elif difference == 0:
                differenceFormatted = '±0.0 kg'
            elif difference < 0:
                differenceFormatted = f'-{format_decimal(abs(difference) / 1000)} kg'
            else:
                differenceFormatted = f'+{format_decimal(difference / 1000)} kg'

            models.append(
                BodyWeightEntryModel(
                    id=entry.id,
                    entry_datetime=entry.datetime,  # type: ignore[arg-type]
                    weight=entry.weight,
                    difference=difference,
                    difference_formatted=differenceFormatted,
                    difference_type=WeightDifferenceType.get_by_difference(difference),
                )
            )
            previousWeight = entry.weight

        models.reverse()
        return models

    @staticmethod
    def add_body_weight_entry(entry_datetime: datetime, weight: int, user_id: int) -> None:
        db.session.add(BodyWeight(datetime=entry_datetime, weight=weight, user_id=user_id))
        db.session.commit()

    @staticmethod
    def update_body_weight_entry(entry: BodyWeight, entry_datetime: datetime, weight: int) -> None:
        entry.datetime = entry_datetime  # type: ignore[assignment]
        entry.weight = weight
        db.session.commit()

    @staticmethod
    def delete_body_weight_entry(entry: BodyWeight) -> None:
        db.session.delete(entry)
        db.session.commit()
