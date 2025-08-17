from flask_login import current_user
from sqlalchemy import Integer, JSON
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column

from sporttracker.logic.model.NotificationProviderType import NotificationProviderType
from sporttracker.logic.model.NotificationType import NotificationType
from sporttracker.logic.model.db import db


class NotificationSettings(db.Model):  # type: ignore[name-defined]
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider_type = db.Column(db.Enum(NotificationProviderType), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_active = db.Column(db.Boolean(), nullable=False)
    notification_types = db.Column(MutableDict.as_mutable(JSON))  # type: ignore[arg-type]

    def __repr__(self):
        return f'NotificationSettings(type: {self.type.name}, user_id: {self.user_id})'

    def get_notification_types(self) -> dict[NotificationType, bool]:
        notificationTypes = {}
        for notificationTypeName, isActive in self.notification_types.items():
            try:
                notificationType = NotificationType(notificationTypeName)  # type: ignore[call-arg]
                notificationTypes[notificationType] = isActive
            except ValueError:
                pass

        return notificationTypes

    def update_missing_values(self) -> bool:
        notificationTypes = self.get_notification_types()

        isUpdated = False
        for notificationType in [t for t in NotificationType]:
            if notificationType not in notificationTypes:
                self.notification_types[notificationType.name] = True
                isUpdated = True

        return isUpdated

    def update(
        self,
        notification_types: dict[NotificationType, bool],
    ):
        self.notification_types = {enumValue.name: isActive for enumValue, isActive in notification_types.items()}


def get_notification_settings_by_user_by_provider_type(
    user_id: int, provider_type: NotificationProviderType
) -> NotificationSettings:
    notificationSettings = (
        NotificationSettings.query.filter(NotificationSettings.user_id == user_id)
        .filter(NotificationSettings.provider_type == provider_type)
        .first()
    )

    if notificationSettings is None:
        raise ValueError(
            f'Could not find notification settings for user id "{user_id}" and provider type "{provider_type}"'
        )

    if notificationSettings.update_missing_values():
        db.session.commit()

    return notificationSettings


def get_notification_settings_by_id(notification_settings_id: int) -> NotificationSettings:
    notificationSettings = (
        NotificationSettings.query.filter(NotificationSettings.user_id == current_user.id)
        .filter(NotificationSettings.id == notification_settings_id)
        .first()
    )

    if notificationSettings is None:
        raise ValueError(f'Could not find notification settings with id "{notification_settings_id}"')

    if notificationSettings.update_missing_values():
        db.session.commit()

    return notificationSettings
