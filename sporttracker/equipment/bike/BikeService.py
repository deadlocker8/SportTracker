from sporttracker.equipment.BaseEquipmentService import BaseEquipmentService
from sporttracker.equipment.bike.BikeEntity import Bike
from sporttracker.equipment.bike.BikeModel import BikeFormModel


class BikeService(BaseEquipmentService[Bike, BikeFormModel]):
    entity_class = Bike
    label = 'bike'
