from flask_login import current_user
from sqlalchemy import Integer, String, Boolean
from sqlalchemy.orm import mapped_column, Mapped

from sporttracker.logic.DateTimeAccess import DateTimeAccess
from sporttracker.logic.model.TrackType import TrackType
from sporttracker.logic.model.db import db


class Maintenance(db.Model, DateTimeAccess):  # type: ignore[name-defined]
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type = db.Column(db.Enum(TrackType))
    description: Mapped[String] = mapped_column(String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_reminder_active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    reminder_limit: Mapped[int] = mapped_column(Integer, nullable=True)

    def __repr__(self):
        return (
            f'Maintenance('
            f'id: {self.id}, '
            f'type: {self.type}, '
            f'description: {self.description}, '
            f'user_id: {self.user_id}, '
            f'is_reminder_active: {self.is_reminder_active}, '
            f'reminder_limit: {self.reminder_limit})'
        )


def get_maintenance_by_id(maintenance_id: int) -> Maintenance | None:
    return (
        Maintenance.query.filter(Maintenance.user_id == current_user.id)
        .filter(Maintenance.id == maintenance_id)
        .first()
    )
