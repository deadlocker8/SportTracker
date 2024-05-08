from dataclasses import dataclass


@dataclass
class Achievement:
    icon: str
    is_font_awesome_icon: bool
    color: str
    title: str
    description: str
