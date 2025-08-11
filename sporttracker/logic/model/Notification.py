from datetime import datetime

import flask_babel
from flask_login import current_user
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


def get_total_number_of_notifications() -> int:
    return Notification.query.filter(Notification.user_id == current_user.id).count()


def get_all_notifications() -> list[Notification]:
    return Notification.query.filter(Notification.user_id == current_user.id).order_by(Notification.id.desc()).all()


def get_notification_by_id(notification_id: int) -> Notification | None:
    return (
        Notification.query.filter(Notification.user_id == current_user.id)
        .filter(Notification.id == notification_id)
        .first()
    )


def add_notification(notification_type: NotificationType, title: str, message: str, item_id: int | None = None) -> None:
    notification = Notification(
        date_time=datetime.now(),
        title=title,
        message=message,
        type=notification_type,
        item_id=item_id,
        user_id=current_user.id,
    )

    db.session.add(notification)
    db.session.commit()
