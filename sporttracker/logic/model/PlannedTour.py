from flask_login import current_user
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
    gpxFileName: Mapped[str] = mapped_column(String, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return (
            f'PlannedTour('
            f'id: {self.id}, '
            f'type: {self.type}, '
            f'name: {self.name}, '
            f'last_edit_date: {self.last_edit_date}, '
            f'gpxFileName: {self.gpxFileName}, '
            f'user_id: {self.user_id})'
        )


def get_planned_tour_by_id(tour_id: int) -> PlannedTour | None:
    return (
        PlannedTour.query.filter(PlannedTour.user_id == current_user.id)
        .filter(PlannedTour.id == tour_id)
        .first()
    )
