from datetime import datetime

from flask_babel import gettext, format_datetime
from flask_login import current_user
from flask_sqlalchemy.pagination import Pagination

from sporttracker.db import db
from sporttracker.helpers import Helpers
from sporttracker.longDistanceTour.LongDistanceTourEntity import LongDistanceTour
from sporttracker.maintenance.MaintenanceEventsCollector import get_maintenances_with_events
from sporttracker.maintenance.MaintenanceFilterStateEntity import MaintenanceFilterState
from sporttracker.monthGoal.MonthGoalEntity import (
    MonthGoalSummary,
    MonthGoalDistanceSummary,
    MonthGoalCountSummary,
    MonthGoalDurationSummary,
)
from sporttracker.monthGoal.MonthGoalService import MonthGoalService
from sporttracker.notification.NotificationEntity import Notification
from sporttracker.notification.NotificationType import NotificationType
from sporttracker.notification.Observable import Observable
from sporttracker.plannedTour.PlannedTourEntity import PlannedTour
from sporttracker.quickFilter.QuickFilterStateEntity import QuickFilterState
from sporttracker.user.UserEntity import User
from sporttracker.workout.WorkoutEntity import Workout
from sporttracker.workout.WorkoutType import WorkoutType
from sporttracker.workout.distance.DistanceWorkoutEntity import DistanceWorkout
from sporttracker.workout.distance.DistanceWorkoutService import DistanceWorkoutService
from sporttracker.workout.fitness.FitnessWorkoutEntity import FitnessWorkout


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

    def on_distance_workout_updated(
        self,
        user_id: int,
        workout: Workout,
        previousLongestDistance: int | None,
    ) -> None:
        user = User.query.filter(User.id == user_id).first()
        if user is None:
            return

        self.__check_maintenance_reminder_limits(user_id, workout.type)
        self.__check_longest_distance_workout(user_id, workout, previousLongestDistance)

    def __check_maintenance_reminder_limits(self, user_id: int, workout_type: WorkoutType) -> None:
        quickFilterState = QuickFilterState().reset(DistanceWorkoutService.get_available_years(user_id))
        quickFilterState.update({t: t == workout_type for t in WorkoutType}, quickFilterState.years)
        maintenances = get_maintenances_with_events(quickFilterState, MaintenanceFilterState(), user_id)
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

    def __check_longest_distance_workout(
        self, user_id: int, workout: DistanceWorkout, previousLongestDistance: int | None
    ) -> None:
        if previousLongestDistance is None:
            return

        if workout.distance <= previousLongestDistance:
            return

        messageTemplate = gettext('You completed a new distance record with {distance} km in one {workoutType} workout')

        self.__add_notification(
            user_id=user_id,
            notification_type=NotificationType.LONGEST_WORKOUT,
            message=messageTemplate.format(
                distance=Helpers.format_decimal(workout.distance / 1000, 2),
                workoutType=workout.type.get_localized_name(),
            ),
            message_details=None,
            item_id=workout.id,
        )

    def on_check_month_goals(
        self, user_id: int, workout: Workout, previousCompletedMonthGoals: list[MonthGoalSummary] | None
    ) -> None:
        if previousCompletedMonthGoals is None:
            return

        year = workout.start_time.year  # type: ignore[attr-defined]
        month = workout.start_time.month  # type: ignore[attr-defined]

        newCompletedGoals = MonthGoalService.get_goal_summaries_new_completed(
            year=year,
            month=month,
            workoutTypes=[workout.type],
            user_id=user_id,
            previous_completed=previousCompletedMonthGoals,
        )

        for goal in newCompletedGoals:
            if isinstance(goal, MonthGoalDistanceSummary):
                self.__on_month_goal_reached(
                    user_id=user_id,
                    year=year,  # type: ignore[attr-defined]
                    month=month,  # type: ignore[attr-defined]
                    workout_type=goal.type,
                    goalName=gettext('distance month goal'),
                    goal_perfect=f'{Helpers.format_decimal(goal.goal_distance_perfect, decimals=1)} km',
                    item_id=goal.id,
                    notification_type=NotificationType.MONTH_GOAL_DISTANCE,
                )
            elif isinstance(goal, MonthGoalCountSummary):
                self.__on_month_goal_reached(
                    user_id=user_id,
                    year=year,
                    month=month,
                    workout_type=goal.type,
                    goalName=gettext('count month goal'),
                    goal_perfect=f'{goal.goal_count_perfect}x',
                    item_id=goal.id,
                    notification_type=NotificationType.MONTH_GOAL_COUNT,
                )
            elif isinstance(goal, MonthGoalDurationSummary):
                self.__on_month_goal_reached(
                    user_id=user_id,
                    year=year,
                    month=month,
                    workout_type=goal.type,
                    goalName=gettext('duration month goal'),
                    goal_perfect=f'{Helpers.format_duration(int(goal.goal_duration_perfect))} h',
                    item_id=goal.id,
                    notification_type=NotificationType.MONTH_GOAL_DURATION,
                )
            else:
                raise ValueError(f'Unsupported month goal summary type "{goal}"')

    def __on_month_goal_reached(
        self,
        user_id: int,
        year: int,
        month: int,
        workout_type: WorkoutType,
        goalName: str,
        goal_perfect: str,
        item_id: int,
        notification_type: NotificationType,
    ) -> None:
        goalDate = datetime(year=year, month=month, day=1)
        messageTemplate = gettext('You completed your {workoutType} {goalName} "{goalPerfect}" for {date}')

        self.__add_notification(
            user_id=user_id,
            notification_type=notification_type,
            message=messageTemplate.format(
                goalName=goalName,
                goalPerfect=goal_perfect,
                workoutType=workout_type.get_localized_name(),
                date=format_datetime(goalDate, format='MMMM yyyy'),
            ),
            message_details=None,
            item_id=item_id,
        )

    def on_duration_workout_updated(self, user_id: int, workout: Workout, previousLongestDuration: int | None) -> None:
        user = User.query.filter(User.id == user_id).first()
        if user is None:
            return

        self.__check_longest_duration_workout(user_id, workout, previousLongestDuration)

    def __check_longest_duration_workout(
        self, user_id: int, workout: FitnessWorkout, previousLongestDuration: int | None
    ) -> None:
        if previousLongestDuration is None:
            return

        if workout.duration <= previousLongestDuration:
            return

        messageTemplate = gettext('You completed a new duration record with {duration} h in one {workoutType}')

        self.__add_notification(
            user_id=user_id,
            notification_type=NotificationType.LONGEST_WORKOUT,
            message=messageTemplate.format(
                duration=Helpers.format_duration(workout.duration), workoutType=workout.type.get_localized_name()
            ),
            message_details=None,
            item_id=workout.id,
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
