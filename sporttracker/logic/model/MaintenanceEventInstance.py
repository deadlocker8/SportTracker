from dataclasses import dataclass
from datetime import datetime

from flask_login import current_user
from sqlalchemy import Integer, DateTime, extract
from sqlalchemy.orm import mapped_column, Mapped

from sporttracker.logic.DateTimeAccess import DateTimeAccess
from sporttracker.logic.model.Maintenance import Maintenance
from sporttracker.logic.model.WorkoutType import WorkoutType
from sporttracker.logic.model.db import db


@dataclass
class MaintenanceEvent(DateTimeAccess):
    id: int
    type: WorkoutType
    description: str
    event_date: datetime

    def get_date_time(self) -> datetime:
        return self.event_date


class MaintenanceEventInstance(db.Model):  # type: ignore[name-defined]
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_date: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    maintenance_id = db.Column(db.Integer, db.ForeignKey('maintenance.id'), nullable=False)

    def get_date(self) -> str:
        return self.event_date.strftime('%Y-%m-%d')  # type: ignore[attr-defined]

    def get_time(self) -> str:
        return self.event_date.strftime('%H:%M')  # type: ignore[attr-defined]

    def __repr__(self):
        return (
            f'MaintenanceEventInstance('
            f'id: {self.id}, '
            f'event_date: {self.event_date}, '
            f'maintenance_id: {self.maintenance_id})'
        )


def get_maintenance_events_by_year_and_month_by_type(
    year: int, month: int, workoutTypes: list[WorkoutType]
) -> list[MaintenanceEvent]:
    rows = (
        MaintenanceEventInstance.query.join(Maintenance)
        .with_entities(
            MaintenanceEventInstance.id,
            Maintenance.type,
            Maintenance.description,
            MaintenanceEventInstance.event_date,
        )
        .filter(Maintenance.user_id == current_user.id)
        .filter(Maintenance.type.in_(workoutTypes))
        .filter(extract('year', MaintenanceEventInstance.event_date) == year)
        .filter(extract('month', MaintenanceEventInstance.event_date) == month)
        .all()
    )

    return [MaintenanceEvent(row[0], row[1], row[2], row[3]) for row in rows]


def get_maintenance_event_by_id(event_id: int) -> MaintenanceEventInstance | None:
    return (
        MaintenanceEventInstance.query.join(Maintenance)
        .filter(Maintenance.user_id == current_user.id)
        .filter(MaintenanceEventInstance.id == event_id)
        .first()
    )


def get_maintenance_events_by_maintenance_id(
    maintenance_id: int, user_id: int
) -> list[MaintenanceEventInstance]:
    return (
        MaintenanceEventInstance.query.join(Maintenance)
        .filter(Maintenance.user_id == user_id)
        .filter(MaintenanceEventInstance.maintenance_id == maintenance_id)
        .order_by(MaintenanceEventInstance.event_date.asc())
        .all()
    )


def get_latest_maintenance_event_by_maintenance_id(maintenance_id: int) -> MaintenanceEventInstance:
    return (
        MaintenanceEventInstance.query.join(Maintenance)
        .filter(Maintenance.user_id == current_user.id)
        .filter(MaintenanceEventInstance.maintenance_id == maintenance_id)
        .order_by(MaintenanceEventInstance.event_date.desc())
        .first()
    )
