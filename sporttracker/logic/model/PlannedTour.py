from sqlalchemy import Integer, DateTime, String
from sqlalchemy.orm import mapped_column, Mapped

from sporttracker.logic.DateTimeAccess import DateTimeAccess
from sporttracker.logic.model.Track import TrackType
from sporttracker.logic.model.db import db


class PlannedTour(db.Model, DateTimeAccess):  # type: ignore[name-defined]
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type = db.Column(db.Enum(TrackType))
    name: Mapped[String] = mapped_column(String, nullable=False)
    last_edit_date: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
