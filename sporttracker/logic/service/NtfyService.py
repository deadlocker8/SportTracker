import logging
from typing import Any

from TheCodeLabs_BaseUtils.NtfyHelper import NtfyHelper
from flask_babel import gettext, force_locale

from sporttracker.logic import Constants
from sporttracker.logic.MaintenanceEventsCollector import (
    get_maintenances_with_events,
    MaintenanceWithEventsModel,
)
from sporttracker.logic.Observable import Listener
from sporttracker.logic.QuickFilterState import QuickFilterState
from sporttracker.logic.model.NtfySettings import NtfySettings
from sporttracker.logic.model.User import User, Language
from sporttracker.logic.model.WorkoutType import WorkoutType

LOGGER = logging.getLogger(Constants.APP_NAME)


class NtfyService(Listener):
    def on_update(self, data: dict[str, Any]) -> None:
        user = User.query.filter(User.id == data['user_id']).first()
        if user is None:
            return

        if not user.isMaintenanceRemindersNotificationsActivated:
            return

        ntfy_settings = user.get_ntfy_settings()

        quickFilterState = QuickFilterState()
        quickFilterState.set_states({t: t == data['workout_type'] for t in WorkoutType})

        maintenances = get_maintenances_with_events(quickFilterState, user.id)
        for maintenance in maintenances:
            if not maintenance.isLimitActive:
                continue

            if not maintenance.isLimitExceeded:
                continue

            try:
                LOGGER.debug(f'Sending ntfy message for user {user.id} and maintenance {maintenance.id}')
                NtfyService.__send_notification(ntfy_settings, maintenance, user.language)
            except Exception as e:
                LOGGER.error(f'Error while sending ntfy message: {e}')

    @staticmethod
    def __send_notification(
        ntfy_settings: NtfySettings,
        maintenance: MaintenanceWithEventsModel,
        language: Language,
    ) -> None:
        with force_locale(language.shortCode):
            message_template = gettext(
                'SportTracker: Maintenance "{name}" exceeds configured limit\n\nLimit: {limit} km, Exceeded by: {limitExceededDistance} km'
            )

            limitExceededDistance = 0
            if maintenance.limitExceededDistance is not None:
                limitExceededDistance = maintenance.limitExceededDistance // 1000

            message = message_template.format(
                name=maintenance.description,
                limit=maintenance.limit // 1000,
                limitExceededDistance=limitExceededDistance,
            )

            NtfyHelper.send_message(
                userName=ntfy_settings.username,
                password=ntfy_settings.password,
                baseUrl=ntfy_settings.server_url,
                topicName=ntfy_settings.topic,
                message=message,
                tags=['bell'],
            )
