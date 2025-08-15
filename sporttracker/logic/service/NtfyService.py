import logging
from typing import Any

from TheCodeLabs_BaseUtils.NtfyHelper import NtfyHelper
from flask_babel import gettext

from sporttracker.logic import Constants
from sporttracker.logic.Observable import Listener
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

        if not user.isMaintenanceRemindersNotificationsActivated:
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
                    'Title': title,
                    'Actions': f'action=view, label={gettext("Show in SportTracker")}, url={notification.type.get_action_url(notification.item_id, external=True)}, clear=true',
                },
            )
        except Exception as e:
            LOGGER.error(f'Error while sending ntfy message: {e}')
