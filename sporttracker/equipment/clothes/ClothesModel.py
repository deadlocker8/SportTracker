from dataclasses import dataclass

from sporttracker.equipment.clothes.ClothesType import ClothesType
from sporttracker.equipment.EquipmentModel import BaseEquipmentFormModel, BaseEquipmentModel


@dataclass
class ClothesModel(BaseEquipmentModel):
    clothes_type: ClothesType


class ClothesFormModel(BaseEquipmentFormModel):
    clothes_type: str
