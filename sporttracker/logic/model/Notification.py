from datetime import datetime

import flask_babel
from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import mapped_column, Mapped

from sporttracker.logic.model.NotificationType import NotificationType
from sporttracker.logic.model.db import db


class Notification(db.Model):  # type: ignore[name-defined]
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date_time: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    title: Mapped[String] = mapped_column(String, nullable=False)
    message: Mapped[String] = mapped_column(String, nullable=False)
    type = db.Column(db.Enum(NotificationType))
    item_id = db.Column(db.Integer, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'Participant(id: {self.id}, name: {self.name}, user_id: {self.user_id})'

    def get_localized_time_delta(self) -> str:
        timedelta = flask_babel.format_timedelta(datetime.now() - self.date_time, 'short')  # type: ignore[operator]
        return flask_babel.gettext(f'{timedelta} ago', timedelta=timedelta)
