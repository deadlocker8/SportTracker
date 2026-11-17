from dataclasses import dataclass
from datetime import date
from typing import Any

from pydantic import BaseModel, field_validator

from sporttracker.equipment.EquipmentEntity import Equipment
from sporttracker.workout.WorkoutType import WorkoutType


@dataclass
class BaseEquipmentModel:
    id: int
    workout_type: WorkoutType
    name: str
    is_owned: bool
    purchase_date: date
    is_active: bool
    inactive_date: date | None


class BaseEquipmentFormModel(BaseModel):
    name: str
    workout_type: str
    is_owned: bool | None = None
    purchase_date: str
    is_active: bool | None = None
    inactive_date: str | None = None

    @field_validator('name', mode='before')
    @classmethod
    def name_strip(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.strip()
        return v


@dataclass
class EquipmentStatisticModel:
    equipment: BaseEquipmentModel
    number_of_workouts: int
    total_duration: int
    total_distance: int | None


@dataclass
class EquipmentGroupModel:
    icon: str
    is_font_awesome_icon: bool
    add_text: str
    add_url: str
    items: list[EquipmentStatisticModel]


@dataclass
class EquipmentSelectionSubGroupModel:
    name: str
    icon: str
    items: list[Equipment]


@dataclass
class EquipmentSelectionGroupModel:
    name: str
    icon: str
    is_font_awesome_icon: bool
    items: list[Equipment]
    sub_groups: list[EquipmentSelectionSubGroupModel]
