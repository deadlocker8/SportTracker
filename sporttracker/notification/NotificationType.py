from __future__ import annotations

import enum
from collections.abc import Callable

from flask import url_for
from flask_babel import gettext
from flask_login import current_user


class NotificationType(enum.Enum):
    MAINTENANCE_REMINDER = ('MAINTENANCE_REMINDER', 'fa-wrench', True, 'bg-danger', 'text-light', 0)
    NEW_SHARED_PLANNED_TOUR = 'NEW_SHARED_PLANNED_TOUR', 'fa-lightbulb', True, 'bg-warning', 'text-dark', 1
    EDITED_SHARED_PLANNED_TOUR = 'EDITED_SHARED_PLANNED_TOUR', 'fa-lightbulb', True, 'bg-warning', 'text-dark', 2
    DELETED_SHARED_PLANNED_TOUR = 'DELETED_SHARED_PLANNED_TOUR', 'fa-lightbulb', True, 'bg-warning', 'text-dark', 3
    REVOKED_SHARED_PLANNED_TOUR = 'REVOKED_SHARED_PLANNED_TOUR', 'fa-lightbulb', True, 'bg-warning', 'text-dark', 4
    NEW_SHARED_LONG_DISTANCE_TOUR = 'NEW_SHARED_LONG_DISTANCE_TOUR', 'fa-lightbulb', True, 'bg-warning', 'text-dark', 5
    EDITED_SHARED_LONG_DISTANCE_TOUR = (
        'EDITED_SHARED_LONG_DISTANCE_TOUR',
        'fa-lightbulb',
        True,
        'bg-warning',
        'text-dark',
        6,
    )
    DELETED_SHARED_LONG_DISTANCE_TOUR = (
        'DELETED_SHARED_LONG_DISTANCE_TOUR',
        'fa-lightbulb',
        True,
        'bg-warning',
        'text-dark',
        7,
    )
    REVOKED_SHARED_LONG_DISTANCE_TOUR = (
        'REVOKED_SHARED_LONG_DISTANCE_TOUR',
        'fa-lightbulb',
        True,
        'bg-warning',
        'text-dark',
        8,
    )
    LONGEST_WORKOUT = 'LONGEST_WORKOUT', 'trophy', False, 'bg-info', 'text-dark', 9
    MONTH_GOAL_DISTANCE = 'MONTH_GOAL_DISTANCE', 'flag', False, 'bg-success', 'text-dark', 10
    MONTH_GOAL_COUNT = 'MONTH_GOAL_COUNT', 'flag', False, 'bg-success', 'text-dark', 11
    MONTH_GOAL_DURATION = 'MONTH_GOAL_DURATION', 'flag', False, 'bg-success', 'text-dark', 12

    icon: str
    is_font_awesome_icon: bool
    color: str
    font_color: str
    order: int

    def __new__(
        cls,
        name: str,
        icon: str,
        is_font_awesome_icon: bool,
        color: str,
        font_color: str,
        order: int,
    ):
        member = object.__new__(cls)
        member._value_ = name
        member.icon = icon
        member.is_font_awesome_icon = is_font_awesome_icon
        member.color = color
        member.font_color = font_color
        member.order = order
        return member

    def get_localized_title(self) -> str:
        # must be done this way to include translations in *.po and *.mo file
        if self == self.MAINTENANCE_REMINDER:
            return gettext('Maintenance limit exceeded')
        elif self == self.NEW_SHARED_PLANNED_TOUR:
            return gettext('New shared planned tour')
        elif self == self.EDITED_SHARED_PLANNED_TOUR:
            return gettext('Updated shared planned tour')
        elif self == self.DELETED_SHARED_PLANNED_TOUR:
            return gettext('Deleted shared planned tour')
        elif self == self.REVOKED_SHARED_PLANNED_TOUR:
            return gettext('Access to shared planned tour revoked')
        elif self == self.NEW_SHARED_LONG_DISTANCE_TOUR:
            return gettext('New shared long-distance tour')
        elif self == self.EDITED_SHARED_LONG_DISTANCE_TOUR:
            return gettext('Updated shared long-distance tour')
        elif self == self.DELETED_SHARED_LONG_DISTANCE_TOUR:
            return gettext('Deleted shared long-distance tour')
        elif self == self.REVOKED_SHARED_LONG_DISTANCE_TOUR:
            return gettext('Access to shared long-distance tour revoked')
        elif self == self.LONGEST_WORKOUT:
            return gettext('New longest workout')
        elif self in [self.MONTH_GOAL_DISTANCE, self.MONTH_GOAL_COUNT, self.MONTH_GOAL_DURATION]:
            return gettext('Month goal reached')

        raise ValueError(f'Could not get localized name for unsupported NotificationType: {self}')

    def get_action_url(self, item_id: int | None, external: bool = False) -> str | None:
        from sporttracker.monthGoal.MonthGoalService import MonthGoalService

        if self == self.MAINTENANCE_REMINDER:
            return url_for('maintenances.showSingleMaintenance', maintenance_id=item_id, _external=external)
        elif self == self.NEW_SHARED_PLANNED_TOUR:
            return url_for('maps.showPlannedTour', tour_id=item_id, _external=external)
        elif self == self.EDITED_SHARED_PLANNED_TOUR:
            return url_for('maps.showPlannedTour', tour_id=item_id, _external=external)
        elif self == self.DELETED_SHARED_PLANNED_TOUR:
            return None
        elif self == self.REVOKED_SHARED_PLANNED_TOUR:
            return None
        elif self == self.NEW_SHARED_LONG_DISTANCE_TOUR:
            return url_for('maps.showLongDistanceTour', tour_id=item_id, _external=external)
        elif self == self.EDITED_SHARED_LONG_DISTANCE_TOUR:
            return url_for('maps.showLongDistanceTour', tour_id=item_id, _external=external)
        elif self == self.DELETED_SHARED_LONG_DISTANCE_TOUR:
            return None
        elif self == self.REVOKED_SHARED_LONG_DISTANCE_TOUR:
            return None
        elif self == self.LONGEST_WORKOUT:
            return url_for('achievements.showAchievements', _external=external)
        elif self == self.MONTH_GOAL_DISTANCE:
            return self.__get_action_url_for_month_goal(
                item_id, external, MonthGoalService.get_month_goal_distance_by_id
            )
        elif self == self.MONTH_GOAL_COUNT:
            return self.__get_action_url_for_month_goal(item_id, external, MonthGoalService.get_month_goal_count_by_id)
        elif self == self.MONTH_GOAL_DURATION:
            return self.__get_action_url_for_month_goal(
                item_id, external, MonthGoalService.get_month_goal_duration_by_id
            )

        raise ValueError(f'Could not get action url for unsupported NotificationType: {self}')

    @staticmethod
    def __get_action_url_for_month_goal(item_id: int | None, external: bool, fetch_method: Callable) -> str | None:
        if item_id is None:
            return None

        monthGoal = fetch_method(item_id, user_id=current_user.id)
        if monthGoal is None:
            return url_for('workouts.listWorkouts', _external=external)

        return url_for('workouts.listWorkouts', year=monthGoal.year, month=monthGoal.month, _external=external)

    @staticmethod
    def get_sorted() -> list[NotificationType]:
        return sorted([n for n in NotificationType], key=lambda entry: entry.order)
