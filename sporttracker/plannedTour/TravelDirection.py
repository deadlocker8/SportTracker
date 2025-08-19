import enum

from flask_babel import gettext


class TravelDirection(enum.Enum):
    SINGLE = 'SINGLE', 'turn_sharp_right', 0
    RETURN = 'RETURN', 'sync_alt', 1
    ROUNDTRIP = 'ROUNDTRIP', 'refresh', 2

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
        if self == self.SINGLE:
            return gettext('Single')
        elif self == self.RETURN:
            return gettext('Return')
        elif self == self.ROUNDTRIP:
            return gettext('Roundtrip')

        raise ValueError(f'Could not get localized name for unsupported TravelDirection: {self}')
