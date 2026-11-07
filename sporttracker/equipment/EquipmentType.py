import enum

from flask_babel import gettext


class EquipmentType(enum.Enum):
    BIKE = 'BIKE', 'fa-bicycle', True, 0
    CLOTHES = 'CLOTHES', 'apparel', False, 1
    CUSTOM = 'CUSTOM', 'shelves', False, 2

    icon: str
    is_font_awesome_icon: bool
    order: int

    def __new__(
        cls,
        name: str,
        icon: str,
        is_font_awesome_icon: bool,
        order: int,
    ):
        member = object.__new__(cls)
        member._value_ = name
        member.icon = icon
        member.is_font_awesome_icon = is_font_awesome_icon
        member.order = order
        return member

    def get_localized_name(self) -> str:
        # must be done this way to include translations in *.po and *.mo file
        if self == self.BIKE:
            return gettext('Bikes')
        elif self == self.CLOTHES:
            return gettext('Clothes')
        elif self == self.CUSTOM:
            return gettext('Custom')

        raise ValueError(f'Could not get localized name for unsupported EquipmentType: {self}')
