import enum

from flask_babel import gettext
from flask_login import current_user
from sqlalchemy import Integer, DateTime, String, Table, Column, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.sql import or_

from sporttracker.logic.DateTimeAccess import DateTimeAccess
from sporttracker.logic.model.Track import TrackType
from sporttracker.logic.model.User import User
from sporttracker.logic.model.db import db


class TravelType(enum.Enum):
    NONE = 'NONE', 'home', 0
    CAR = 'CAR', 'directions_car', 1
    TRAIN = 'TRAIN', 'train', 2

    icon: str
    order: int

    def __new__(
        cls,
        name: str,
        icon: str,
        order: int,
    ):
        member = object.__new__(cls)
        member._value_ = name
        member.icon = icon
        member.order = order
        return member

    def get_localized_name(self) -> str:
        # must be done this way to include translations in *.po and *.mo file
        if self == self.NONE:
            return gettext('none')
        elif self == self.CAR:
            return gettext('Car')
        elif self == self.TRAIN:
            return gettext('Train')

        raise ValueError(f'Could not get localized name for unsupported TravelType: {self}')


class TravelDirection(enum.Enum):
    SINGLE = 'SINGLE', 'turn_sharp_right', 0
    RETURN = 'RETURN', 'sync_alt', 1
    ROUNDTRIP = 'ROUNDTRIP', 'refresh', 2

    icon: str
    order: int

    def __new__(
        cls,
        name: str,
        icon: str,
        order: int,
    ):
        member = object.__new__(cls)
        member._value_ = name
        member.icon = icon
        member.order = order
        return member

    def get_localized_name(self) -> str:
        # must be done this way to include translations in *.po and *.mo file
        if self == self.SINGLE:
            return gettext('Single')
        elif self == self.RETURN:
            return gettext('Return')
        elif self == self.ROUNDTRIP:
            return gettext('Roundtrip')

        raise ValueError(f'Could not get localized name for unsupported TravelDirection: {self}')


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
    creation_date: Mapped[DateTime] = mapped_column(DateTime)
    last_edit_date: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    gpxFileName: Mapped[str] = mapped_column(String, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    shared_users: Mapped[list[User]] = relationship(secondary=planned_tour_user_association)
    arrival_method = db.Column(db.Enum(TravelType))
    departure_method = db.Column(db.Enum(TravelType))
    direction = db.Column(db.Enum(TravelDirection))

    def __repr__(self):
        return (
            f'PlannedTour('
            f'id: {self.id}, '
            f'type: {self.type}, '
            f'name: {self.name}, '
            f'creation_date: {self.creation_date}, '
            f'last_edit_date: {self.last_edit_date}, '
            f'gpxFileName: {self.gpxFileName}, '
            f'user_id: {self.user_id}, '
            f'shared_users: {[user.id for user in self.shared_users]}, '
            f'arrival_method: {self.arrival_method}, '
            f'departure_method: {self.departure_method}, '
            f'direction: {self.direction})'
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
