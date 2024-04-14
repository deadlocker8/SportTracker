from sqlalchemy import Integer, DateTime, String
from sqlalchemy.orm import mapped_column, Mapped

from sporttracker.logic.model.Track import TrackType
from sporttracker.logic.model.db import db


class MaintenanceEvent(db.Model):  # type: ignore[name-defined]
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type = db.Column(db.Enum(TrackType))
    event_date: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    description: Mapped[String] = mapped_column(String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
