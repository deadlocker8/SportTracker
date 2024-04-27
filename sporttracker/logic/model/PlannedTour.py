from flask_login import current_user
from sqlalchemy import Integer, DateTime, String, Table, Column, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.sql import or_

from sporttracker.logic.DateTimeAccess import DateTimeAccess
from sporttracker.logic.model.Track import TrackType
from sporttracker.logic.model.User import User
from sporttracker.logic.model.db import db

planned_tour_user_association = Table(
    'planned_tour_user_association',
    db.Model.metadata,
    Column('planned_tour_id', ForeignKey('planned_tour.id')),
    Column('user_id', ForeignKey('user.id')),
)


class PlannedTour(db.Model, DateTimeAccess):  # type: ignore[name-defined]
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type = db.Column(db.Enum(TrackType))
    name: Mapped[String] = mapped_column(String, nullable=False)
    last_edit_date: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    gpxFileName: Mapped[str] = mapped_column(String, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    shared_users: Mapped[list[User]] = relationship(secondary=planned_tour_user_association)

    def __repr__(self):
        return (
            f'PlannedTour('
            f'id: {self.id}, '
            f'type: {self.type}, '
            f'name: {self.name}, '
            f'last_edit_date: {self.last_edit_date}, '
            f'gpxFileName: {self.gpxFileName}, '
            f'user_id: {self.user_id}, '
            f'shared_users: {[user.id for user in self.shared_users]})'
        )


def get_planned_tour_by_id(tour_id: int) -> PlannedTour | None:
    return (
        PlannedTour.query.filter(
            or_(
                PlannedTour.user_id == current_user.id,
                PlannedTour.shared_users.any(id=current_user.id),
            )
        )
        .filter(PlannedTour.id == tour_id)
        .first()
    )
