from sqlalchemy import Integer, String, Column, ForeignKey, Table
from sqlalchemy.orm import mapped_column, Mapped

from sporttracker.logic.model.db import db


class Participant(db.Model):  # type: ignore[name-defined]
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[String] = mapped_column(String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


track_participant_association = Table(
    'track_participant_association',
    db.Model.metadata,
    Column('track_id', ForeignKey('track.id')),
    Column('participant_id', ForeignKey('participant.id')),
)
