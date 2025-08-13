from sqlalchemy import Integer, DateTime, String, Table, Column, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from sporttracker.logic.DateTimeAccess import DateTimeAccess
from sporttracker.logic.model.GpxMetadata import GpxMetadata
from sporttracker.logic.model.TravelDirection import TravelDirection
from sporttracker.logic.model.TravelType import TravelType
from sporttracker.logic.model.User import User, get_user_by_id
from sporttracker.logic.model.WorkoutType import WorkoutType
from sporttracker.logic.model.db import db

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

    def get_owner_name(self) -> str:
        user = get_user_by_id(self.user_id)
        return user.username


distance_workout_planned_tour_association = Table(
    'distance_workout_planned_tour_association',
    db.Model.metadata,
    Column('distance_workout_id', ForeignKey('distance_workout.id')),
    Column('planned_tour_id', ForeignKey('planned_tour.id')),
)
