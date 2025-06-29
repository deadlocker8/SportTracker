from operator import attrgetter

import natsort
from flask_login import current_user
from natsort import natsorted
from sqlalchemy import Integer, DateTime, String, Table, Column, ForeignKey, asc, func
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.sql import or_

from sporttracker.logic.DateTimeAccess import DateTimeAccess
from sporttracker.logic.model.GpxMetadata import GpxMetadata
from sporttracker.logic.model.TravelDirection import TravelDirection
from sporttracker.logic.model.TravelType import TravelType
from sporttracker.logic.model.User import User
from sporttracker.logic.model.WorkoutType import WorkoutType
from sporttracker.logic.model.db import db
from sporttracker.logic.model.filterStates.PlannedTourFilterState import PlannedTourFilterState

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


def get_new_planned_tour_ids() -> list[int]:
    if not current_user.is_authenticated:
        return []

    last_viewed_date = User.query.filter(User.id == current_user.id).first().planned_tours_last_viewed_date

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

    last_viewed_date = User.query.filter(User.id == current_user.id).first().planned_tours_last_viewed_date

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
    plannedTours = (
        PlannedTour.query.filter(
            or_(
                PlannedTour.user_id == current_user.id,
                PlannedTour.shared_users.any(id=current_user.id),
            )
        )
        .filter(PlannedTour.type.in_(workoutTypes))
        .all()
    )

    return natsorted(plannedTours, alg=natsort.ns.IGNORECASE, key=attrgetter('name'))


def get_planned_tours_by_ids(ids: list[int]) -> list[PlannedTour]:
    return [p for p in get_planned_tours(WorkoutType.get_distance_workout_types()) if p.id in ids]


def get_planned_tours_filtered(
    workoutTypes: list[WorkoutType], plannedTourFilterState: 'PlannedTourFilterState'
) -> list[PlannedTour]:
    plannedToursQuery = (
        PlannedTour.query.filter(
            or_(
                PlannedTour.user_id == current_user.id,
                PlannedTour.shared_users.any(id=current_user.id),
            )
        )
        .filter(PlannedTour.type.in_(workoutTypes))
        .filter(PlannedTour.arrival_method.in_(plannedTourFilterState.get_selected_arrival_methods()))
        .filter(PlannedTour.departure_method.in_(plannedTourFilterState.get_selected_departure_methods()))
        .filter(PlannedTour.direction.in_(plannedTourFilterState.get_selected_directions()))
    )

    if plannedTourFilterState.name_filter is not None:
        plannedToursQuery = plannedToursQuery.filter(PlannedTour.name.icontains(plannedTourFilterState.name_filter))

    plannedToursQuery = plannedToursQuery.order_by(asc(func.lower(PlannedTour.name)))
    plannedTours = plannedToursQuery.all()

    plannedTours = __filter_by_distance(
        plannedTours,
        plannedTourFilterState.minimum_distance,  # type: ignore[arg-type]
        plannedTourFilterState.maximum_distance,  # type: ignore[arg-type]
    )

    plannedTours = __filter_by_status(
        plannedTours,
        plannedTourFilterState.is_done_selected,  # type: ignore[arg-type]
        plannedTourFilterState.is_todo_selected,  # type: ignore[arg-type]
    )

    plannedTours = __filter_by_long_distance_tours(
        plannedTours,
        plannedTourFilterState.is_long_distance_tours_include_selected,  # type: ignore[arg-type]
        plannedTourFilterState.is_long_distance_tours_exclude_selected,  # type: ignore[arg-type]
    )

    return natsorted(plannedTours, alg=natsort.ns.IGNORECASE, key=attrgetter('name'))


def __filter_by_distance(
    plannedTours: list[PlannedTour],
    minimumDistance: int | None,
    maximumDistance: int | None,
) -> list[PlannedTour]:
    if minimumDistance is None and maximumDistance is None:
        return plannedTours

    filteredTours = []
    for plannedTour in plannedTours:
        gpxMetadata = plannedTour.get_gpx_metadata()
        if gpxMetadata is None:
            continue

        if minimumDistance is not None and gpxMetadata.length < minimumDistance:
            continue

        if maximumDistance is not None and gpxMetadata.length > maximumDistance:
            continue

        filteredTours.append(plannedTour)

    return filteredTours


def __filter_by_status(plannedTours: list[PlannedTour], includeDone: bool, includeTodo: bool) -> list[PlannedTour]:
    if includeDone and includeTodo:
        return plannedTours

    from sporttracker.logic.model.DistanceWorkout import DistanceWorkout

    filteredTours = []
    for plannedTour in plannedTours:
        numberOfLinkedWorkouts = (
            DistanceWorkout.query.filter(DistanceWorkout.user_id == current_user.id)
            .filter(DistanceWorkout.planned_tour == plannedTour)
            .order_by(DistanceWorkout.start_time.asc())
            .count()
        )

        if includeDone and numberOfLinkedWorkouts > 0:
            filteredTours.append(plannedTour)
            continue

        if includeTodo and numberOfLinkedWorkouts == 0:
            filteredTours.append(plannedTour)

    return filteredTours


def __filter_by_long_distance_tours(
    plannedTours: list[PlannedTour], includeLongDistanceTours: bool, excludeLongDistanceTours: bool
) -> list[PlannedTour]:
    if includeLongDistanceTours and excludeLongDistanceTours:
        return plannedTours

    from sporttracker.logic.model.LongDistanceTour import (
        LongDistanceTourPlannedTourAssociation,
        get_long_distance_tour_by_id,
    )

    filteredTours = []

    for plannedTour in plannedTours:
        longDistanceTours = LongDistanceTourPlannedTourAssociation.query.filter(
            LongDistanceTourPlannedTourAssociation.planned_tour_id == plannedTour.id
        ).all()

        numberOfAllowedLongDistanceTours = 0
        for longDistanceTourAssociation in longDistanceTours:
            longDistanceTour = get_long_distance_tour_by_id(longDistanceTourAssociation.long_distance_tour_id)
            if longDistanceTour is None:
                continue

            if current_user.id == longDistanceTour.user_id:
                numberOfAllowedLongDistanceTours += 1
                continue

            sharedUserIds = [u.id for u in longDistanceTour.shared_users]
            if current_user.id in sharedUserIds:
                numberOfAllowedLongDistanceTours += 1

        if includeLongDistanceTours and numberOfAllowedLongDistanceTours > 0:
            filteredTours.append(plannedTour)
            continue

        if excludeLongDistanceTours and numberOfAllowedLongDistanceTours == 0:
            filteredTours.append(plannedTour)

    return filteredTours


distance_workout_planned_tour_association = Table(
    'distance_workout_planned_tour_association',
    db.Model.metadata,
    Column('distance_workout_id', ForeignKey('distance_workout.id')),
    Column('planned_tour_id', ForeignKey('planned_tour.id')),
)
