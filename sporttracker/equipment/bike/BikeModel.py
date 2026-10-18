from dataclasses import dataclass

from sporttracker.equipment.EquipmentModel import BaseEquipmentFormModel, BaseEquipmentModel


@dataclass
class BikeModel(BaseEquipmentModel):
    pass


class BikeFormModel(BaseEquipmentFormModel):
    pass
