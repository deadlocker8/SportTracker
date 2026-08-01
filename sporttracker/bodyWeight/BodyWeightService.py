from __future__ import annotations

from datetime import datetime

from sporttracker.bodyWeight.BodyWeightEntity import BodyWeight
from sporttracker.db import db


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
