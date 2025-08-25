from sporttracker.notification.NotificationSettingsEntity import NotificationSettings
from sporttracker.notification.NotificationType import NotificationType


class TestNotificationSettings:
    def test_update_missing_values(self) -> None:
        notificationSettings = NotificationSettings()
        notificationSettings.notification_types = {}
        assert len(notificationSettings.notification_types) == 0

        notificationSettings.update_missing_values()
        assert notificationSettings.get_notification_types() == {
            NotificationType.MAINTENANCE_REMINDER: True,
            NotificationType.NEW_SHARED_PLANNED_TOUR: True,
            NotificationType.EDITED_SHARED_PLANNED_TOUR: True,
            NotificationType.DELETED_SHARED_PLANNED_TOUR: True,
            NotificationType.REVOKED_SHARED_PLANNED_TOUR: True,
            NotificationType.NEW_SHARED_LONG_DISTANCE_TOUR: True,
            NotificationType.EDITED_SHARED_LONG_DISTANCE_TOUR: True,
            NotificationType.DELETED_SHARED_LONG_DISTANCE_TOUR: True,
            NotificationType.REVOKED_SHARED_LONG_DISTANCE_TOUR: True,
            NotificationType.LONGEST_WORKOUT: True,
            NotificationType.MONTH_GOAL_DISTANCE: True,
            NotificationType.MONTH_GOAL_COUNT: True,
            NotificationType.MONTH_GOAL_DURATION: True,
        }

    def test_update(self) -> None:
        notificationSettings = NotificationSettings()
        notificationSettings.update(
            {
                NotificationType.MAINTENANCE_REMINDER: False,
                NotificationType.NEW_SHARED_PLANNED_TOUR: True,
                NotificationType.EDITED_SHARED_PLANNED_TOUR: False,
                NotificationType.DELETED_SHARED_PLANNED_TOUR: True,
                NotificationType.REVOKED_SHARED_PLANNED_TOUR: False,
                NotificationType.NEW_SHARED_LONG_DISTANCE_TOUR: False,
                NotificationType.EDITED_SHARED_LONG_DISTANCE_TOUR: False,
                NotificationType.DELETED_SHARED_LONG_DISTANCE_TOUR: False,
                NotificationType.REVOKED_SHARED_LONG_DISTANCE_TOUR: False,
                NotificationType.LONGEST_WORKOUT: False,
                NotificationType.MONTH_GOAL_DISTANCE: True,
                NotificationType.MONTH_GOAL_COUNT: False,
                NotificationType.MONTH_GOAL_DURATION: True,
            },
        )

        assert notificationSettings.get_notification_types() == {
            NotificationType.MAINTENANCE_REMINDER: False,
            NotificationType.NEW_SHARED_PLANNED_TOUR: True,
            NotificationType.EDITED_SHARED_PLANNED_TOUR: False,
            NotificationType.DELETED_SHARED_PLANNED_TOUR: True,
            NotificationType.REVOKED_SHARED_PLANNED_TOUR: False,
            NotificationType.NEW_SHARED_LONG_DISTANCE_TOUR: False,
            NotificationType.EDITED_SHARED_LONG_DISTANCE_TOUR: False,
            NotificationType.DELETED_SHARED_LONG_DISTANCE_TOUR: False,
            NotificationType.REVOKED_SHARED_LONG_DISTANCE_TOUR: False,
            NotificationType.LONGEST_WORKOUT: False,
            NotificationType.MONTH_GOAL_DISTANCE: True,
            NotificationType.MONTH_GOAL_COUNT: False,
            NotificationType.MONTH_GOAL_DURATION: True,
        }
