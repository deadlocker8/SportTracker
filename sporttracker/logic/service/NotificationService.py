from datetime import datetime

from flask_babel import gettext
from flask_login import current_user

from sporttracker.logic.MaintenanceEventsCollector import get_maintenances_with_events
from sporttracker.logic.Observable import Observable
from sporttracker.logic.model.DistanceWorkout import get_available_years
from sporttracker.logic.model.Notification import Notification
from sporttracker.logic.model.NotificationType import NotificationType
from sporttracker.logic.model.PlannedTour import PlannedTour
from sporttracker.logic.model.User import User
from sporttracker.logic.model.WorkoutType import WorkoutType
from sporttracker.logic.model.db import db
from sporttracker.logic.model.filterStates.MaintenanceFilterState import MaintenanceFilterState
from sporttracker.logic.model.filterStates.QuickFilterState import QuickFilterState


class NotificationService(Observable):
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

    def __add_notification(
        self,
        user_id: int,
        notification_type: NotificationType,
        message: str,
        message_details: str | None,
        item_id: int | None = None,
    ) -> None:
        notification = Notification(
            date_time=datetime.now(),
            message=message,
            message_details=message_details,
            type=notification_type,
            item_id=item_id,
            user_id=user_id,
        )

        db.session.add(notification)
        db.session.commit()

        self._notify_listeners({'notification': notification})

    def on_distance_workout_updated(self, user_id: int, workout_type: WorkoutType) -> None:
        user = User.query.filter(User.id == user_id).first()
        if user is None:
            return

        quickFilterState = QuickFilterState().reset(get_available_years(user.id))
        quickFilterState.update({t: t == workout_type for t in WorkoutType}, quickFilterState.years)

        maintenances = get_maintenances_with_events(quickFilterState, MaintenanceFilterState(), user.id)
        for maintenance in maintenances:
            if not maintenance.isLimitActive:
                continue

            if not maintenance.isLimitExceeded:
                continue

            limitExceededDistance = 0
            if maintenance.limitExceededDistance is not None:
                limitExceededDistance = maintenance.limitExceededDistance // 1000

            messageTemplate = gettext('Maintenance "{name}" exceeds configured limit')
            messageDetailsTemplate = gettext('Limit: {limit} km, Exceeded by: {limitExceededDistance} km')

            self.__add_notification(
                user_id=user_id,
                notification_type=NotificationType.MAINTENANCE_REMINDER,
                message=messageTemplate.format(name=maintenance.description),
                message_details=messageDetailsTemplate.format(
                    limit=maintenance.limit // 1000, limitExceededDistance=limitExceededDistance
                ),
                item_id=maintenance.id,
            )

    def on_planned_tour_created(self, planned_tour: PlannedTour) -> None:
        owner = User.query.filter(User.id == planned_tour.user_id).first()
        if owner is None:
            return

        for user in planned_tour.shared_users:
            messageTemplate = gettext('{owner} has shared the planned tour "{tour_name}" with you')

            self.__add_notification(
                user_id=user.id,
                notification_type=NotificationType.NEW_SHARED_PLANNED_TOUR,
                message=messageTemplate.format(owner=owner.username.capitalize(), tour_name=planned_tour.name),
                message_details=None,
                item_id=planned_tour.id,
            )

    def on_planned_tour_updated(self, planned_tour: PlannedTour) -> None:
        owner = User.query.filter(User.id == planned_tour.user_id).first()
        if owner is None:
            return

        for user in planned_tour.shared_users:
            messageTemplate = gettext('{owner} has updated the planned tour "{tour_name}"')

            self.__add_notification(
                user_id=user.id,
                notification_type=NotificationType.EDITED_SHARED_PLANNED_TOUR,
                message=messageTemplate.format(owner=owner.username.capitalize(), tour_name=planned_tour.name),
                message_details=None,
                item_id=planned_tour.id,
            )
