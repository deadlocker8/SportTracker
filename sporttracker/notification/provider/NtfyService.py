import logging
from typing import Any

from TheCodeLabs_BaseUtils.NtfyHelper import NtfyHelper
from flask_babel import gettext

from sporttracker.logic import Constants
from sporttracker.logic.Observable import Listener
from sporttracker.notification.provider.NotificationProviderType import NotificationProviderType
from sporttracker.notification.NotificationSettingsEntity import get_notification_settings_by_user_by_provider_type
from sporttracker.logic.model.User import User

LOGGER = logging.getLogger(Constants.APP_NAME)


class NtfyService(Listener):
    def on_update(self, data: dict[str, Any]) -> None:
        """
        Expected data:
        {
        'notification': Notification.class
        }
        """
        notification = data['notification']

        user = User.query.filter(User.id == notification.user_id).first()
        if user is None:
            return

        try:
            notification_settings = get_notification_settings_by_user_by_provider_type(
                user.id, NotificationProviderType.NTFY
            )
        except ValueError as e:
            LOGGER.error(e)
            return

        if not notification_settings.is_active:
            return

        if not notification_settings.get_notification_types()[notification.type]:
            return

        ntfy_settings = user.get_ntfy_settings()

        title = f'{Constants.APP_NAME}: {notification.type.get_localized_title()}'
        message = notification.message
        if notification.message_details is not None:
            message = f'{message}\n\n{notification.message_details}'

        try:
            LOGGER.debug(f'Sending ntfy message of type {notification.type.name} for user {user.id}')
            NtfyHelper.send_message(
                userName=ntfy_settings.username,
                password=ntfy_settings.password,
                baseUrl=ntfy_settings.server_url,
                topicName=ntfy_settings.topic,
                message=message,
                tags=['bell'],
                headers={
                    'Title': title.encode('utf-8'),
                    'Actions': f'action=view, label={gettext("Show in SportTracker")}, url={notification.type.get_action_url(notification.item_id, external=True)}, clear=true'.encode(
                        'utf-8'
                    ),
                },
            )
        except Exception as e:
            LOGGER.error(f'Error while sending ntfy message: {e}')
