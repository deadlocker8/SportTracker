from __future__ import annotations

import enum

from flask_babel import gettext


class EquipmentType(enum.Enum):
    CLOTHES = 'CLOTHES', 'apparel', False, 0
    BIKE = 'BIKE', 'fa-bicycle', True, 1
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
        member.order = order
        return member

    def get_localized_name(self) -> str:
        # must be done this way to include translations in *.po and *.mo file
        if self == self.CLOTHES:
            return gettext('Clothes')
        elif self == self.BIKE:
            return gettext('Bike')

        raise ValueError(f'Could not get localized name for unsupported EquipmentType: {self}')
