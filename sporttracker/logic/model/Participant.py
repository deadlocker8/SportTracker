from flask_login import current_user
from sqlalchemy import Integer, String, Column, ForeignKey, Table
from sqlalchemy.orm import mapped_column, Mapped

from sporttracker.logic.model.db import db


class Participant(db.Model):  # type: ignore[name-defined]
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[String] = mapped_column(String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'Participant(' f'id: {self.id}, ' f'name: {self.name}, ' f'user_id: {self.user_id})'


track_participant_association = Table(
    'track_participant_association',
    db.Model.metadata,
    Column('track_id', ForeignKey('track.id')),
    Column('participant_id', ForeignKey('participant.id')),
)


def get_participants_by_ids(ids: list[int]) -> list[Participant]:
    participants = (
        Participant.query.filter(Participant.user_id == current_user.id)
        .filter(Participant.id.in_(ids))
        .all()
    )
    return participants


def get_participants() -> list[Participant]:
    return (
        Participant.query.filter(Participant.user_id == current_user.id)
        .order_by(Participant.name.asc())
        .all()
    )
