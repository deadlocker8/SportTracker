from datetime import datetime

from flask_babel import gettext
from flask_login import current_user
from flask_sqlalchemy.pagination import Pagination

from sporttracker.logic.MaintenanceEventsCollector import get_maintenances_with_events
from sporttracker.logic.Observable import Observable
from sporttracker.logic.model.DistanceWorkout import get_available_years
from sporttracker.logic.model.LongDistanceTour import LongDistanceTour
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
    def get_notifications_paginated(page_number: int) -> Pagination:
        return db.paginate(
            Notification.query.filter(Notification.user_id == current_user.id).order_by(Notification.id.desc()),
            per_page=10,
            page=page_number,
            error_out=False,
        )

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
        self.__on_tour_create_or_deleted(
            planned_tour,
            gettext('{owner} has shared the planned tour "{tour_name}" with you'),
            NotificationType.NEW_SHARED_PLANNED_TOUR,
            True,
        )

    def on_planned_tour_updated(self, planned_tour: PlannedTour, previous_shared_users: list[User]) -> None:
        self.__on_tour_updated(
            tour=planned_tour,
            previous_shared_users=previous_shared_users,
            notification_type_new=NotificationType.NEW_SHARED_PLANNED_TOUR,
            message_template_new=gettext('{owner} has shared the planned tour "{tour_name}" with you'),
            notification_type_updated=NotificationType.EDITED_SHARED_PLANNED_TOUR,
            message_template_updated=gettext('{owner} has updated the planned tour "{tour_name}"'),
            notification_type_revoked=NotificationType.REVOKED_SHARED_PLANNED_TOUR,
            message_template_revoked=gettext('{owner} has revoked your access to the planned tour "{tour_name}"'),
        )

    def on_planned_tour_deleted(self, planned_tour: PlannedTour) -> None:
        self.__on_tour_create_or_deleted(
            planned_tour,
            gettext('{owner} has deleted the planned tour "{tour_name}"'),
            NotificationType.DELETED_SHARED_PLANNED_TOUR,
            False,
        )

    def on_long_distance_tour_created(self, long_distance_tour: LongDistanceTour) -> None:
        self.__on_tour_create_or_deleted(
            long_distance_tour,
            gettext('{owner} has shared the long-distance tour "{tour_name}" with you'),
            NotificationType.NEW_SHARED_LONG_DISTANCE_TOUR,
            True,
        )

    def on_long_distance_tour_updated(self, planned_tour: PlannedTour, previous_shared_users: list[User]) -> None:
        self.__on_tour_updated(
            tour=planned_tour,
            previous_shared_users=previous_shared_users,
            notification_type_new=NotificationType.NEW_SHARED_LONG_DISTANCE_TOUR,
            message_template_new=gettext('{owner} has shared the long-distance tour "{tour_name}" with you'),
            notification_type_updated=NotificationType.EDITED_SHARED_LONG_DISTANCE_TOUR,
            message_template_updated=gettext('{owner} has updated the long-distance tour "{tour_name}"'),
            notification_type_revoked=NotificationType.REVOKED_SHARED_LONG_DISTANCE_TOUR,
            message_template_revoked=gettext('{owner} has revoked your access to the long-distance tour "{tour_name}"'),
        )

    def on_long_distance_tour_deleted(self, long_distance_tour: LongDistanceTour) -> None:
        self.__on_tour_create_or_deleted(
            long_distance_tour,
            gettext('{owner} has deleted the long-distance tour "{tour_name}"'),
            NotificationType.DELETED_SHARED_LONG_DISTANCE_TOUR,
            False,
        )

    def __on_tour_create_or_deleted(
        self,
        tour: PlannedTour | LongDistanceTour,
        message_template: str,
        notification_type: NotificationType,
        include_item_id: bool = True,
    ) -> None:
        owner = User.query.filter(User.id == tour.user_id).first()
        if owner is None:
            return

        for user in tour.shared_users:
            self.__add_notification(
                user_id=user.id,
                notification_type=notification_type,
                message=message_template.format(owner=owner.username.capitalize(), tour_name=tour.name),
                message_details=None,
                item_id=tour.id if include_item_id else None,
            )

    def __on_tour_updated(
        self,
        tour: PlannedTour | LongDistanceTour,
        previous_shared_users: list[User],
        notification_type_new: NotificationType,
        message_template_new: str,
        notification_type_updated: NotificationType,
        message_template_updated: str,
        notification_type_revoked: NotificationType,
        message_template_revoked: str,
    ) -> None:
        owner = User.query.filter(User.id == tour.user_id).first()
        if owner is None:
            return

        for user in previous_shared_users:
            if user not in tour.shared_users:
                self.__add_notification(
                    user_id=user.id,
                    notification_type=notification_type_revoked,
                    message=message_template_revoked.format(
                        owner=current_user.username.capitalize(), tour_name=tour.name
                    ),
                    message_details=None,
                    item_id=None,
                )

        for user in tour.shared_users:
            if user not in previous_shared_users:
                self.__add_notification(
                    user_id=user.id,
                    notification_type=notification_type_new,
                    message=message_template_new.format(owner=current_user.username.capitalize(), tour_name=tour.name),
                    message_details=None,
                    item_id=tour.id,
                )
                continue

            if user.id == current_user.id:
                continue

            self.__add_notification(
                user_id=user.id,
                notification_type=notification_type_updated,
                message=message_template_updated.format(owner=current_user.username.capitalize(), tour_name=tour.name),
                message_details=None,
                item_id=tour.id,
            )

        if owner.id != current_user.id:
            self.__add_notification(
                user_id=owner.id,
                notification_type=notification_type_updated,
                message=message_template_updated.format(owner=current_user.username.capitalize(), tour_name=tour.name),
                message_details=None,
                item_id=tour.id,
            )
