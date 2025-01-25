from dataclasses import dataclass
from datetime import datetime

from flask_login import current_user
from sqlalchemy import Integer, String, DateTime, extract, func, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from sporttracker.logic.model.GpxMetadata import GpxMetadata
from sporttracker.logic.model.PlannedTour import (
    PlannedTour,
    distance_sport_planned_tour_association,
)
from sporttracker.logic.model.Sport import Sport
from sporttracker.logic.model.SportType import SportType
from sporttracker.logic.model.db import db


class DistanceSport(Sport):  # type: ignore[name-defined]
    __tablename__ = 'distance_sport'
    id: Mapped[int] = mapped_column(ForeignKey('sport.id'), primary_key=True)
    distance: Mapped[int] = mapped_column(Integer, nullable=False)
    average_heart_rate: Mapped[int] = mapped_column(Integer, nullable=True)
    elevation_sum: Mapped[int] = mapped_column(Integer, nullable=True)
    share_code: Mapped[str] = mapped_column(String, nullable=True)
    gpx_metadata_id = db.Column(db.Integer, db.ForeignKey('gpx_metadata.id'), nullable=True)
    planned_tour: Mapped[PlannedTour] = relationship(
        secondary=distance_sport_planned_tour_association
    )

    __mapper_args__ = {
        'polymorphic_identity': 'distance_sport',
    }

    def __repr__(self):
        return (
            f'DistanceSport('
            f'name: {self.name}, '
            f'start_time: {self.start_time}, '
            f'duration: {self.duration}, '
            f'custom_fields: {self.custom_fields}, '
            f'participants: {self.participants}, '
            f'user_id: {self.user_id})'
            f'distance: {self.distance}, '
            f'average_heart_rate: {self.average_heart_rate}, '
            f'elevation_sum: {self.elevation_sum}, '
            f'custom_fields: {self.custom_fields}, '
            f'participants: {self.participants}, '
            f'user_id: {self.user_id}, '
            f'share_code: {self.share_code},'
            f'gpx_metadata_id: {self.gpx_metadata_id})'
        )

    def get_gpx_metadata(self) -> GpxMetadata | None:
        if self.gpx_metadata_id is None:
            return None
        else:
            return GpxMetadata.query.get(self.gpx_metadata_id)

    def get_download_name(self) -> str:
        escapedName = ''.join([c if c.isalnum() else '_' for c in str(self.name)])
        return f'{self.id} - {escapedName}'


def get_number_of_all_distance_sports() -> int:
    return DistanceSport.query.count()


@dataclass
class MonthDistanceSum:
    year: int
    month: int
    distanceSum: float


def get_distance_per_month_by_type(
    sportType: SportType, minYear: int, maxYear: int
) -> list[MonthDistanceSum]:
    year = extract('year', DistanceSport.start_time)
    month = extract('month', DistanceSport.start_time)

    rows = (
        DistanceSport.query.with_entities(
            func.sum(DistanceSport.distance / 1000).label('distanceSum'),
            year.label('year'),
            month.label('month'),
        )
        .filter(DistanceSport.type == sportType)
        .filter(DistanceSport.user_id == current_user.id)
        .group_by(year, month)
        .order_by(year, month)
        .all()
    )

    result = []
    for currentYear in range(minYear, maxYear + 1):
        for currentMonth in range(1, 13):
            for row in rows:
                if row.year == currentYear and row.month == currentMonth:
                    result.append(
                        MonthDistanceSum(
                            year=currentYear, month=currentMonth, distanceSum=float(row.distanceSum)
                        )
                    )
                    break
            else:
                result.append(
                    MonthDistanceSum(year=currentYear, month=currentMonth, distanceSum=0.0)
                )

    return result


def get_available_years(userId) -> list[int]:
    year = extract('year', DistanceSport.start_time)

    rows = (
        DistanceSport.query.with_entities(year.label('year'))
        .filter(DistanceSport.user_id == userId)
        .group_by(year)
        .order_by(year)
        .all()
    )

    if rows is None:
        return []

    return [int(row.year) for row in rows]


def get_distance_between_dates(
    startDateTime: datetime | DateTime,
    endDateTime: datetime | DateTime,
    sportTypes: list[SportType],
) -> int:
    return int(
        DistanceSport.query.with_entities(func.sum(DistanceSport.distance))
        .filter(DistanceSport.type.in_(sportTypes))
        .filter(DistanceSport.user_id == current_user.id)
        .filter(DistanceSport.start_time.between(startDateTime, endDateTime))
        .scalar()
        or 0
    )


def get_distance_sport_by_id(distance_sport_id: int) -> DistanceSport | None:
    return (
        DistanceSport.query.filter(DistanceSport.user_id == current_user.id)
        .filter(DistanceSport.id == distance_sport_id)
        .first()
    )


def get_distance_sport_by_share_code(shareCode: str) -> DistanceSport | None:
    return DistanceSport.query.filter(DistanceSport.share_code == shareCode).first()


def get_distance_sport_ids_by_planned_tour(plannedTour: PlannedTour) -> list[int]:
    linkedIds = (
        DistanceSport.query.with_entities(DistanceSport.id)
        .filter(DistanceSport.user_id == current_user.id)
        .filter(DistanceSport.planned_tour == plannedTour)
        .all()
    )

    if linkedIds is None:
        return []

    return [int(row.id) for row in linkedIds]
