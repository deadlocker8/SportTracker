from sqlalchemy import JSON, Boolean
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column

from sporttracker.db import db
from sporttracker.equipment.clothes.ClothesType import ClothesType
from sporttracker.equipment.EquipmentType import EquipmentType


class EquipmentFilterState(db.Model):  # type: ignore[name-defined]
    __tablename__ = 'filter_state_equipment'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, primary_key=True)
    equipment_types = db.Column(MutableDict.as_mutable(JSON))  # type: ignore[arg-type]
    clothes_types = db.Column(MutableDict.as_mutable(JSON))  # type: ignore[arg-type]
    is_active_selected: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_inactive_selected: Mapped[bool] = mapped_column(Boolean, nullable=False)

    def __repr__(self):
        return (
            f'EquipmentFilterState('
            f'user_id: {self.user_id}, '
            f'equipment_types: {self.equipment_types}, '
            f'clothes_types: {self.clothes_types}, '
            f'is_active_selected: {self.is_active_selected}, '
            f'is_inactive_selected: {self.is_inactive_selected})'
        )

    def get_equipment_types(self) -> dict[EquipmentType, bool]:
        equipmentTypes = {}
        for equipmentTypeName, isActive in (self.equipment_types or {}).items():
            try:
                equipmentType = EquipmentType(equipmentTypeName)  # type: ignore[call-arg]
                equipmentTypes[equipmentType] = isActive
            except ValueError:
                pass

        return equipmentTypes

    def get_selected_equipment_types(self) -> list[EquipmentType]:
        selectedItems = [equipmentType for equipmentType, isActive in self.get_equipment_types().items() if isActive]
        return sorted(selectedItems, key=lambda entry: entry.order)

    def get_clothes_types(self) -> dict[ClothesType, bool]:
        clothesTypes = {}
        for clothesTypeName, isActive in (self.clothes_types or {}).items():
            try:
                clothesType = ClothesType(clothesTypeName)  # type: ignore[call-arg]
                clothesTypes[clothesType] = isActive
            except ValueError:
                pass

        return clothesTypes

    def get_selected_clothes_types(self) -> list[ClothesType]:
        selectedItems = [clothesType for clothesType, isActive in self.get_clothes_types().items() if isActive]
        return sorted(selectedItems, key=lambda entry: entry.order)

    def update(
        self,
        equipment_types: dict[EquipmentType, bool],
        clothes_types: dict[ClothesType, bool],
        is_active_selected: bool,
        is_inactive_selected: bool,
    ):
        self.equipment_types = {enumValue.name: isActive for enumValue, isActive in equipment_types.items()}
        self.clothes_types = {enumValue.name: isActive for enumValue, isActive in clothes_types.items()}
        self.is_active_selected = is_active_selected
        self.is_inactive_selected = is_inactive_selected

    def reset(self) -> None:
        self.update(
            {equipmentType: True for equipmentType in EquipmentType},
            {clothesType: True for clothesType in ClothesType},
            True,
            True,
        )

    def update_missing_values(self) -> bool:
        isUpdated = False

        if self.equipment_types is None:
            self.equipment_types = {}

        if self.clothes_types is None:
            self.clothes_types = {}

        for equipmentType in [t for t in EquipmentType]:
            if equipmentType.name not in self.equipment_types:
                self.equipment_types[equipmentType.name] = True
                isUpdated = True

        for clothesType in [t for t in ClothesType]:
            if clothesType.name not in self.clothes_types:
                self.clothes_types[clothesType.name] = True
                isUpdated = True

        return isUpdated

    def is_any_filter_active(self) -> bool:
        if not self.is_active_selected:
            return True

        if not self.is_inactive_selected:
            return True

        if not all((self.equipment_types or {}).values()):
            return True

        return not all((self.clothes_types or {}).values())


def get_equipment_filter_state_by_user(user_id: int) -> EquipmentFilterState:
    equipmentFilterState = EquipmentFilterState.query.filter(EquipmentFilterState.user_id == user_id).first()

    if equipmentFilterState.update_missing_values():
        db.session.commit()

    return equipmentFilterState
