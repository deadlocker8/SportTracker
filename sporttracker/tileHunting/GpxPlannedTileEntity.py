from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from sporttracker.db import db


class GpxPlannedTile(db.Model):  # type: ignore[name-defined]
    planned_tour_id: Mapped[int] = mapped_column(
        ForeignKey('planned_tour.id', ondelete='CASCADE'), nullable=False, primary_key=True
    )
    x: Mapped[int] = mapped_column(Integer, nullable=False, primary_key=True)
    y: Mapped[int] = mapped_column(Integer, nullable=False, primary_key=True)
