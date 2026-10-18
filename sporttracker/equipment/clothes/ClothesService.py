from typing import cast

from sporttracker.equipment.BaseEquipmentService import BaseEquipmentService, TEntity, TForm
from sporttracker.equipment.clothes.ClothesEntity import Clothes
from sporttracker.equipment.clothes.ClothesModel import ClothesFormModel
from sporttracker.equipment.clothes.ClothesType import ClothesType


class ClothesService(BaseEquipmentService[Clothes, ClothesFormModel]):
    entity_class = Clothes
    label = 'clothes'

    @classmethod
    def _apply_extra_fields(cls, entity: TEntity, form: TForm) -> None:
        clothes = cast(Clothes, entity)
        clothesForm = cast(ClothesFormModel, form)
        clothes.clothes_type = ClothesType(clothesForm.clothes_type)  # type: ignore[call-arg]
