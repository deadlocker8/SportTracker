import enum

from flask_babel import gettext


class TravelType(enum.Enum):
    NONE = 'NONE', 'home', 0
    CAR = 'CAR', 'directions_car', 1
    TRAIN = 'TRAIN', 'train', 2

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
        if self == self.NONE:
            return gettext('None')
        elif self == self.CAR:
            return gettext('Car')
        elif self == self.TRAIN:
            return gettext('Train')

        raise ValueError(f'Could not get localized name for unsupported TravelType: {self}')
