from sporttracker.equipment.clothes.ClothesType import ClothesType
from sporttracker.equipment.EquipmentFilterStateEntity import EquipmentFilterState
from sporttracker.equipment.EquipmentType import EquipmentType


class TestEquipmentFilterState:
    def test_reset(self) -> None:
        equipmentFilterState = EquipmentFilterState()
        equipmentFilterState.update(
            {t: False for t in EquipmentType},
            {t: False for t in ClothesType},
            False,
            False,
        )

        equipmentFilterState.reset()

        assert equipmentFilterState.equipment_types == {t.name: True for t in EquipmentType}
        assert equipmentFilterState.clothes_types == {t.name: True for t in ClothesType}
        assert equipmentFilterState.is_active_selected is True
        assert equipmentFilterState.is_inactive_selected is True

    def test_get_selected_equipment_types(self) -> None:
        equipmentFilterState = EquipmentFilterState()
        equipmentFilterState.equipment_types = {
            EquipmentType.BIKE.name: False,
            EquipmentType.CLOTHES.name: True,
            EquipmentType.CUSTOM.name: False,
        }
        assert equipmentFilterState.get_selected_equipment_types() == [EquipmentType.CLOTHES]

    def test_get_selected_clothes_types(self) -> None:
        equipmentFilterState = EquipmentFilterState()
        equipmentFilterState.clothes_types = {
            ClothesType.HEADGEAR.name: False,
            ClothesType.TOPS.name: True,
            ClothesType.SHOES.name: True,
        }
        assert equipmentFilterState.get_selected_clothes_types() == [ClothesType.TOPS, ClothesType.SHOES]

    def test_update_missing_values(self) -> None:
        equipmentFilterState = EquipmentFilterState()
        equipmentFilterState.equipment_types = {}
        equipmentFilterState.clothes_types = {}
        assert equipmentFilterState.update_missing_values() is True
        assert equipmentFilterState.equipment_types == {t.name: True for t in EquipmentType}
        assert equipmentFilterState.clothes_types == {t.name: True for t in ClothesType}

    def test_is_any_filter_active(self) -> None:
        equipmentFilterState = EquipmentFilterState()
        equipmentFilterState.reset()
        assert equipmentFilterState.is_any_filter_active() is False

        equipmentFilterState.is_active_selected = False
        assert equipmentFilterState.is_any_filter_active() is True
