from datetime import datetime

from flask_login import current_user

from sporttracker.logic.model.Notification import Notification
from sporttracker.logic.model.NotificationType import NotificationType
from sporttracker.logic.model.db import db


class NotificationService:
    @staticmethod
    def get_total_number_of_notifications() -> int:
        if not current_user.is_authenticated:
            return 0

        return Notification.query.filter(Notification.user_id == current_user.id).count()

    @staticmethod
    def get_all_notifications() -> list[Notification]:
        return Notification.query.filter(Notification.user_id == current_user.id).order_by(Notification.id.desc()).all()

    @staticmethod
    def get_notification_by_id(notification_id: int) -> Notification | None:
        return (
            Notification.query.filter(Notification.user_id == current_user.id)
            .filter(Notification.id == notification_id)
            .first()
        )

    @staticmethod
    def add_notification(
        notification_type: NotificationType, title: str, message: str, item_id: int | None = None
    ) -> None:
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
