from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime

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
    LESS = 'LESS', 'trending_down', 'text-success'
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


class BodyWeightService:
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
    def update_body_weight_entry(entry: BodyWeight, date: datetime, weight: int) -> None:
        entry.date = date
        entry.weight = weight
        db.session.commit()

    @staticmethod
    def delete_body_weight_entry(entry: BodyWeight) -> None:
        db.session.delete(entry)
        db.session.commit()
