import enum
from typing import TYPE_CHECKING

from flask_babel import gettext
from flask_login import current_user
from sqlalchemy import Integer, DateTime, String, Table, Column, ForeignKey, asc, func
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.sql import or_

from sporttracker.logic.DateTimeAccess import DateTimeAccess
from sporttracker.logic.model.GpxMetadata import GpxMetadata
from sporttracker.logic.model.User import User
from sporttracker.logic.model.WorkoutType import WorkoutType
from sporttracker.logic.model.db import db

if TYPE_CHECKING:
    from sporttracker.logic.PlannedTourFilterState import PlannedTourFilterState


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
            return gettext('None')
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
    type = db.Column(db.Enum(WorkoutType))
    name: Mapped[String] = mapped_column(String, nullable=False)
    creation_date: Mapped[DateTime] = mapped_column(DateTime)
    last_edit_date: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    last_edit_user_id: Mapped[int] = mapped_column(Integer, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    shared_users: Mapped[list[User]] = relationship(secondary=planned_tour_user_association)
    arrival_method = db.Column(db.Enum(TravelType))
    departure_method = db.Column(db.Enum(TravelType))
    direction = db.Column(db.Enum(TravelDirection))
    share_code: Mapped[str] = mapped_column(String, nullable=True)
    gpx_metadata_id = db.Column(db.Integer, db.ForeignKey('gpx_metadata.id'), nullable=True)

    def __repr__(self):
        return (
            f'PlannedTour('
            f'id: {self.id}, '
            f'type: {self.type}, '
            f'name: {self.name}, '
            f'creation_date: {self.creation_date}, '
            f'last_edit_date: {self.last_edit_date}, '
            f'last_edit_user_id: {self.last_edit_user_id}, '
            f'user_id: {self.user_id}, '
            f'shared_users: {[user.id for user in self.shared_users]}, '
            f'arrival_method: {self.arrival_method}, '
            f'departure_method: {self.departure_method}, '
            f'direction: {self.direction}, '
            f'share_code: {self.share_code},'
            f'gpx_metadata_id: {self.gpx_metadata_id})'
        )

    def get_download_name(self) -> str:
        return ''.join([c if c.isalnum() else '_' for c in str(self.name)])

    def get_gpx_metadata(self) -> GpxMetadata | None:
        if self.gpx_metadata_id is None:
            return None
        else:
            return GpxMetadata.query.get(self.gpx_metadata_id)


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


def get_planned_tour_by_share_code(shareCode: str) -> PlannedTour | None:
    return PlannedTour.query.filter(PlannedTour.share_code == shareCode).first()


def get_new_planned_tour_ids() -> list[int]:
    if not current_user.is_authenticated:
        return []

    last_viewed_date = (
        User.query.filter(User.id == current_user.id).first().planned_tours_last_viewed_date
    )

    rows = (
        PlannedTour.query.with_entities(PlannedTour.id)
        .filter(PlannedTour.shared_users.any(id=current_user.id))
        .filter(PlannedTour.creation_date > last_viewed_date)
        .all()
    )

    return [int(row[0]) for row in rows]


def get_updated_planned_tour_ids() -> list[int]:
    if not current_user.is_authenticated:
        return []

    last_viewed_date = (
        User.query.filter(User.id == current_user.id).first().planned_tours_last_viewed_date
    )

    rows = (
        PlannedTour.query.with_entities(PlannedTour.id)
        .filter(
            or_(
                PlannedTour.user_id == current_user.id,
                PlannedTour.shared_users.any(id=current_user.id),
            )
        )
        .filter(PlannedTour.creation_date != PlannedTour.last_edit_date)
        .filter(PlannedTour.last_edit_user_id != current_user.id)
        .filter(PlannedTour.last_edit_date > last_viewed_date)
        .all()
    )

    return [int(row[0]) for row in rows]


def get_planned_tours(workoutTypes: list[WorkoutType]) -> list[PlannedTour]:
    return (
        PlannedTour.query.filter(
            or_(
                PlannedTour.user_id == current_user.id,
                PlannedTour.shared_users.any(id=current_user.id),
            )
        )
        .filter(PlannedTour.type.in_(workoutTypes))
        .order_by(asc(func.lower(PlannedTour.name)))
        .all()
    )


def get_planned_tours_filtered(
    workoutTypes: list[WorkoutType], plannedTourFilterState: 'PlannedTourFilterState'
) -> list[PlannedTour]:
    return (
        PlannedTour.query.filter(
            or_(
                PlannedTour.user_id == current_user.id,
                PlannedTour.shared_users.any(id=current_user.id),
            )
        )
        .filter(PlannedTour.type.in_(workoutTypes))
        .filter(
            PlannedTour.arrival_method.in_(plannedTourFilterState.get_selected_arrival_methods())
        )
        .filter(
            PlannedTour.departure_method.in_(
                plannedTourFilterState.get_selected_departure_methods()
            )
        )
        .filter(PlannedTour.direction.in_(plannedTourFilterState.get_selected_directions()))
        .order_by(asc(func.lower(PlannedTour.name)))
        .all()
    )


distance_workout_planned_tour_association = Table(
    'distance_workout_planned_tour_association',
    db.Model.metadata,
    Column('distance_workout_id', ForeignKey('distance_workout.id')),
    Column('planned_tour_id', ForeignKey('planned_tour.id')),
)
