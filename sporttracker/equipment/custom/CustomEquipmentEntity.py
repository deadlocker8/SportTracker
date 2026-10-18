from typing import ClassVar

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from sporttracker.equipment.EquipmentEntity import Equipment


class CustomEquipment(Equipment):  # type: ignore[name-defined]
    __tablename__ = 'equipment_custom'
    id: Mapped[int] = mapped_column(ForeignKey('equipment.id', ondelete='CASCADE'), primary_key=True)

    __mapper_args__: ClassVar[dict[str, str]] = {
        'polymorphic_identity': 'equipment_custom',
    }

    @staticmethod
    def get_icon() -> tuple[str, bool]:
        return 'shelves', False
