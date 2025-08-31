from sqlalchemy import Integer, DateTime
from sqlalchemy.orm import mapped_column, Mapped

from sporttracker.db import db


class HeartRateEntity(db.Model):  # type: ignore[name-defined]
    __tablename__ = 'heart_rate_data'
    workout_id: Mapped[int] = mapped_column(Integer, nullable=False, primary_key=True, index=True)
    timestamp: Mapped[DateTime] = mapped_column(DateTime, nullable=False, primary_key=True)
    bpm: Mapped[int] = mapped_column(Integer, nullable=False, primary_key=True)
