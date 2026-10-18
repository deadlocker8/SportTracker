import enum

from flask_babel import gettext


class ClothesType(enum.Enum):
    HEADGEAR = 'HEADGEAR', 0
    TOPS = 'TOPS', 1
    GLOVES = 'GLOVES', 2
    BOTTOMS = 'BOTTOMS', 3
    SHOES = 'SHOES', 4
    MISC = 'MISC', 5

    order: int

    def __new__(
        cls,
        name: str,
        order: int,
    ):
        member = object.__new__(cls)
        member._value_ = name
        member.order = order
        return member

    def get_localized_name(self) -> str:
        # must be done this way to include translations in *.po and *.mo file
        if self == self.HEADGEAR:
            return gettext('Headgear')
        elif self == self.TOPS:
            return gettext('Tops')
        elif self == self.GLOVES:
            return gettext('Gloves')
        elif self == self.BOTTOMS:
            return gettext('Bottoms')
        elif self == self.SHOES:
            return gettext('Shoes')
        elif self == self.MISC:
            return gettext('Misc')

        raise ValueError(f'Could not get localized name for unsupported ClothesType: {self}')
