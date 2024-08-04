from datetime import datetime

from flask_login import current_user
from sqlalchemy import Integer, DateTime, String, extract
from sqlalchemy.orm import mapped_column, Mapped

from sporttracker.logic.DateTimeAccess import DateTimeAccess
from sporttracker.logic.model.TrackType import TrackType
from sporttracker.logic.model.db import db


class MaintenanceEvent(db.Model, DateTimeAccess):  # type: ignore[name-defined]
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type = db.Column(db.Enum(TrackType))
    event_date: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    description: Mapped[String] = mapped_column(String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def get_date(self) -> str:
        return self.event_date.strftime('%Y-%m-%d')  # type: ignore[attr-defined]

    def get_time(self) -> str:
        return self.event_date.strftime('%H:%M')  # type: ignore[attr-defined]

    def get_date_time(self) -> datetime:
        return self.event_date  # type: ignore[return-value]

    def __repr__(self):
        return (
            f'MaintenanceEvent('
            f'id: {self.id}, '
            f'type: {self.type}, '
            f'description: {self.description}, '
            f'user_id: {self.user_id})'
        )


def get_maintenance_events_by_year_and_month_by_type(
    year: int, month: int, trackTypes: list[TrackType]
) -> list[MaintenanceEvent]:
    return (
        MaintenanceEvent.query.filter(MaintenanceEvent.user_id == current_user.id)
        .filter(MaintenanceEvent.type.in_(trackTypes))
        .filter(extract('year', MaintenanceEvent.event_date) == year)
        .filter(extract('month', MaintenanceEvent.event_date) == month)
        .all()
    )


def get_maintenance_event_by_id(event_id: int) -> MaintenanceEvent | None:
    return (
        MaintenanceEvent.query.filter(MaintenanceEvent.user_id == current_user.id)
        .filter(MaintenanceEvent.id == event_id)
        .first()
    )
