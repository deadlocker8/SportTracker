from typing import ClassVar

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from sporttracker.equipment.EquipmentEntity import Equipment


class Clothes(Equipment):  # type: ignore[name-defined]
    __tablename__ = 'equipment_clothes'
    id: Mapped[int] = mapped_column(ForeignKey('equipment.id', ondelete='CASCADE'), primary_key=True)

    __mapper_args__: ClassVar[dict[str, str]] = {
        'polymorphic_identity': 'equipment_clothes',
    }

    @classmethod
    def get_icon(cls) -> tuple[str, bool]:
        return 'shelves', False
