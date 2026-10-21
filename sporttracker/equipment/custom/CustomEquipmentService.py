from sporttracker.equipment.BaseEquipmentService import BaseEquipmentService
from sporttracker.equipment.custom.CustomEquipmentEntity import CustomEquipment
from sporttracker.equipment.custom.CustomEquipmentModel import CustomEquipmentFormModel


class CustomEquipmentService(BaseEquipmentService[CustomEquipment, CustomEquipmentFormModel]):
    entity_class = CustomEquipment
    label = 'custom equipment'
