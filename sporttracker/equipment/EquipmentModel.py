from dataclasses import dataclass
from datetime import date
from typing import Any

from pydantic import BaseModel, field_validator

from sporttracker.workout.WorkoutType import WorkoutType


@dataclass
class BaseEquipmentModel:
    id: int
    workout_type: WorkoutType
    name: str
    purchase_date: date
    is_active: bool
    inactive_date: date | None


class BaseEquipmentFormModel(BaseModel):
    name: str
    workout_type: str
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
class EquipmentGroupModel:
    name: str
    icon: str
    is_font_awesome_icon: bool
    add_url: str
    items: list[BaseEquipmentModel]
