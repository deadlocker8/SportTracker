import enum

from flask_babel import gettext


class WorkoutType(enum.Enum):
    DURATION_BASED = (
        'DURATION_BASED',
        'update',
        0,
    )
    REPETITION_BASED = (
        'REPETITION_BASED',
        'repeat',
        1,
    )

    icon: str
    order: int

    def __new__(
        cls,
        name: str,
        icon: str,
        order: int,
    ):
        member = object.__new__(cls)
        member._value_ = name
        member.icon = icon
        member.order = order
        return member

    def get_localized_name(self) -> str:
        # must be done this way to include translations in *.po and *.mo file
        if self == self.DURATION_BASED:
            return gettext('Time-based')
        elif self == self.REPETITION_BASED:
            return gettext('Repetition-based')

        raise ValueError(f'Could not get localized name for unsupported WorkoutType: {self}')
