from sqlalchemy import DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column

from sporttracker.db import db


class HeartRateEntity(db.Model):  # type: ignore[name-defined]
    __tablename__ = 'heart_rate_data'
    workout_id: Mapped[int] = mapped_column(Integer, nullable=False, primary_key=True, index=True)
    timestamp: Mapped[DateTime] = mapped_column(DateTime, nullable=False, primary_key=True)
    bpm: Mapped[int] = mapped_column(Integer, nullable=False, primary_key=True)
