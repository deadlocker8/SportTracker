from sqlalchemy import Integer
from sqlalchemy.orm import mapped_column, Mapped

from sporttracker.logic.model.db import db


class GpxVisitedTile(db.Model):  # type: ignore[name-defined]
    workout_id: Mapped[int] = mapped_column(Integer, nullable=False, primary_key=True)
    x: Mapped[int] = mapped_column(Integer, nullable=False, primary_key=True)
    y: Mapped[int] = mapped_column(Integer, nullable=False, primary_key=True)
