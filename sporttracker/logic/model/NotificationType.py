import enum

from flask import url_for
from flask_babel import gettext


class NotificationType(enum.Enum):
    MAINTENANCE_REMINDER = (
        'MAINTENANCE_REMINDER',
        'fa-wrench',
        True,
        'bg-danger',
        'text-light',
    )
    NEW_SHARED_PLANNED_TOUR = 'NEW_SHARED_PLANNED_TOUR', 'fa-lightbulb', True, 'bg-primary', 'text-light'
    EDITED_SHARED_PLANNED_TOUR = 'EDITED_SHARED_PLANNED_TOUR', 'fa-lightbulb', True, 'bg-primary', 'text-light'
    DELETED_SHARED_PLANNED_TOUR = 'DELETED_SHARED_PLANNED_TOUR', 'fa-lightbulb', True, 'bg-primary', 'text-light'
    REVOKED_SHARED_PLANNED_TOUR = 'REVOKED_SHARED_PLANNED_TOUR', 'fa-lightbulb', True, 'bg-primary', 'text-light'
    NEW_SHARED_LONG_DISTANCE_TOUR = 'NEW_SHARED_LONG_DISTANCE_TOUR', 'fa-lightbulb', True, 'bg-primary', 'text-light'
    EDITED_SHARED_LONG_DISTANCE_TOUR = (
        'EDITED_SHARED_LONG_DISTANCE_TOUR',
        'fa-lightbulb',
        True,
        'bg-primary',
        'text-light',
    )
    DELETED_SHARED_LONG_DISTANCE_TOUR = (
        'DELETED_SHARED_LONG_DISTANCE_TOUR',
        'fa-lightbulb',
        True,
        'bg-primary',
        'text-light',
    )
    REVOKED_SHARED_LONG_DISTANCE_TOUR = (
        'REVOKED_SHARED_LONG_DISTANCE_TOUR',
        'fa-lightbulb',
        True,
        'bg-primary',
        'text-light',
    )

    icon: str
    is_font_awesome_icon: bool
    color: str
    font_color: str

    def __new__(
        cls,
        name: str,
        icon: str,
        is_font_awesome_icon: bool,
        color: str,
        font_color: str,
    ):
        member = object.__new__(cls)
        member._value_ = name
        member.icon = icon
        member.is_font_awesome_icon = is_font_awesome_icon
        member.color = color
        member.font_color = font_color
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

        raise ValueError(f'Could not get localized name for unsupported NotificationType: {self}')

    def get_action_url(self, item_id: int | None) -> str | None:
        if self == self.MAINTENANCE_REMINDER:
            return url_for('maintenances.showSingleMaintenance', maintenance_id=item_id)
        elif self == self.NEW_SHARED_PLANNED_TOUR:
            return url_for('maps.showPlannedTour', tour_id=item_id)
        elif self == self.EDITED_SHARED_PLANNED_TOUR:
            return url_for('maps.showPlannedTour', tour_id=item_id)
        elif self == self.DELETED_SHARED_PLANNED_TOUR:
            return None
        elif self == self.REVOKED_SHARED_PLANNED_TOUR:
            return None
        elif self == self.NEW_SHARED_LONG_DISTANCE_TOUR:
            return url_for('maps.showLongDistanceTour', tour_id=item_id)
        elif self == self.EDITED_SHARED_LONG_DISTANCE_TOUR:
            return url_for('maps.showLongDistanceTour', tour_id=item_id)
        elif self == self.DELETED_SHARED_LONG_DISTANCE_TOUR:
            return None
        elif self == self.REVOKED_SHARED_LONG_DISTANCE_TOUR:
            return None

        raise ValueError(f'Could not get action url for unsupported NotificationType: {self}')
