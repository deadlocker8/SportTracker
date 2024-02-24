from sqlalchemy import Integer, String
from sqlalchemy.orm import mapped_column, Mapped

from sporttracker.logic.model.db import db


class Participant(db.Model):  # type: ignore[name-defined]
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[String] = mapped_column(String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
