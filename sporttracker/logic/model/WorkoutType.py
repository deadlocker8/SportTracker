from __future__ import annotations

import enum
from datetime import datetime

from flask_babel import gettext


class WorkoutType(enum.Enum):
    BIKING = (
        'BIKING',
        'directions_bike',
        False,
        'bg-warning',
        '#FFC107',
        'border-warning',
        'text-warning',
        '#FFC10796',
        True,
        0,
    )
    RUNNING = (
        'RUNNING',
        'directions_run',
        False,
        'bg-info',
        '#0DCAF0',
        'border-info',
        'text-info',
        '#0DCAF080',
        False,
        1,
    )
    HIKING = (
        'HIKING',
        'hiking',
        False,
        'bg-green',
        '#6BBDA5',
        'border-green',
        'text-green',
        '#39B856AA',
        True,
        2,
    )
    FITNESS = (
        'FITNESS',
        'fitness_center',
        False,
        'bg-purple',
        '#AB87FF',
        'border-purple',
        'text-purple',
        '#39B856AA',
        True,
        3,
    )

    icon: str
    is_font_awesome_icon: bool
    background_color: str
    background_color_hex: str
    border_color: str
    text_color: str
    tile_color: str
    render_speed_in_kph: bool
    order: int

    def __new__(
        cls,
        name: str,
        icon: str,
        is_font_awesome_icon: bool,
        background_color: str,
        background_color_hex: str,
        border_color: str,
        text_color: str,
        tile_color: str,
        render_speed_in_kph: bool,
        order: int,
    ):
        member = object.__new__(cls)
        member._value_ = name
        member.icon = icon
        member.is_font_awesome_icon = is_font_awesome_icon
        member.background_color = background_color
        member.background_color_hex = background_color_hex
        member.border_color = border_color
        member.text_color = text_color
        member.tile_color = tile_color
        member.render_speed_in_kph = render_speed_in_kph
        member.order = order
        return member

    def get_localized_name(self) -> str:
        # must be done this way to include translations in *.po and *.mo file
        if self == self.BIKING:
            return gettext('Biking')
        elif self == self.RUNNING:
            return gettext('Running')
        elif self == self.HIKING:
            return gettext('Hiking')
        elif self == self.FITNESS:
            return gettext('Workout')

        raise ValueError(f'Could not get localized name for unsupported WorkoutType: {self}')

    @staticmethod
    def is_easter_egg_activated() -> bool:
        now = datetime.now()
        return now.month == 4 and now.day == 1

    @staticmethod
    def get_distance_workout_types() -> list[WorkoutType]:
        return [WorkoutType.BIKING, WorkoutType.RUNNING, WorkoutType.HIKING]

    @staticmethod
    def get_fitness_workout_types() -> list[WorkoutType]:
        return [WorkoutType.FITNESS]
