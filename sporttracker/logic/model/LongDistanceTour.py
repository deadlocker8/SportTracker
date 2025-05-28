from operator import attrgetter

import natsort
from flask_login import current_user
from natsort import natsorted
from sqlalchemy import Integer, DateTime, String, Table, Column, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.sql import or_

from sporttracker.logic.DateTimeAccess import DateTimeAccess
from sporttracker.logic.model.User import User
from sporttracker.logic.model.WorkoutType import WorkoutType
from sporttracker.logic.model.db import db

long_distance_tour_user_association = Table(
    'long_distance_tour_user_association',
    db.Model.metadata,
    Column('long_distance_tour_id', ForeignKey('long_distance_tour.id')),
    Column('user_id', ForeignKey('user.id')),
)


class LongDistanceTourPlannedTourAssociation(db.Model):  # type: ignore[name-defined]
    long_distance_tour_id: Mapped[int] = mapped_column(ForeignKey('long_distance_tour.id'), primary_key=True)
    planned_tour_id: Mapped[int] = mapped_column(ForeignKey('planned_tour.id'), primary_key=True)
    order: Mapped[int]


class LongDistanceTour(db.Model, DateTimeAccess):  # type: ignore[name-defined]
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type = db.Column(db.Enum(WorkoutType))
    name: Mapped[String] = mapped_column(String, nullable=False)
    creation_date: Mapped[DateTime] = mapped_column(DateTime)
    last_edit_date: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    last_edit_user_id: Mapped[int] = mapped_column(Integer, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    shared_users: Mapped[list[User]] = relationship(secondary=long_distance_tour_user_association)
    linked_planned_tours: Mapped[list['LongDistanceTourPlannedTourAssociation']] = relationship(
        cascade='all,delete-orphan'
    )

    def __repr__(self):
        return (
            f'LongDistanceTour('
            f'id: {self.id}, '
            f'type: {self.type}, '
            f'name: {self.name}, '
            f'creation_date: {self.creation_date}, '
            f'last_edit_date: {self.last_edit_date}, '
            f'last_edit_user_id: {self.last_edit_user_id}, '
            f'user_id: {self.user_id}, '
            f'shared_users: {[user.id for user in self.shared_users]}, '
            f'linked_planned_tours: {[p.planned_tour_id for p in self.linked_planned_tours]})'
        )


def get_long_distance_tour_by_id(tour_id: int) -> LongDistanceTour | None:
    return (
        LongDistanceTour.query.filter(
            or_(
                LongDistanceTour.user_id == current_user.id,
                LongDistanceTour.shared_users.any(id=current_user.id),
            )
        )
        .filter(LongDistanceTour.id == tour_id)
        .first()
    )


def get_new_long_distance_tour_ids() -> list[int]:
    if not current_user.is_authenticated:
        return []

    last_viewed_date = User.query.filter(User.id == current_user.id).first().long_distance_tours_last_viewed_date

    rows = (
        LongDistanceTour.query.with_entities(LongDistanceTour.id)
        .filter(LongDistanceTour.shared_users.any(id=current_user.id))
        .filter(LongDistanceTour.creation_date > last_viewed_date)
        .all()
    )

    return [int(row[0]) for row in rows]


def get_updated_long_distance_tour_ids() -> list[int]:
    if not current_user.is_authenticated:
        return []

    last_viewed_date = User.query.filter(User.id == current_user.id).first().long_distance_tours_last_viewed_date

    rows = (
        LongDistanceTour.query.with_entities(LongDistanceTour.id)
        .filter(
            or_(
                LongDistanceTour.user_id == current_user.id,
                LongDistanceTour.shared_users.any(id=current_user.id),
            )
        )
        .filter(LongDistanceTour.creation_date != LongDistanceTour.last_edit_date)
        .filter(LongDistanceTour.last_edit_user_id != current_user.id)
        .filter(LongDistanceTour.last_edit_date > last_viewed_date)
        .all()
    )

    return [int(row[0]) for row in rows]


def get_long_distance_tours(workoutTypes: list[WorkoutType]) -> list[LongDistanceTour]:
    longDistanceTours = (
        LongDistanceTour.query.filter(
            or_(
                LongDistanceTour.user_id == current_user.id,
                LongDistanceTour.shared_users.any(id=current_user.id),
            )
        )
        .filter(LongDistanceTour.type.in_(workoutTypes))
        .all()
    )

    return natsorted(longDistanceTours, alg=natsort.ns.IGNORECASE, key=attrgetter('name'))
