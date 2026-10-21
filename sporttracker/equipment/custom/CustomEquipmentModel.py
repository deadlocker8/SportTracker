from dataclasses import dataclass

from sporttracker.equipment.EquipmentModel import BaseEquipmentFormModel, BaseEquipmentModel


@dataclass
class CustomEquipmentModel(BaseEquipmentModel):
    pass


class CustomEquipmentFormModel(BaseEquipmentFormModel):
    pass
