from typing import Any

from pydantic import BaseModel, field_validator


class EquipmentPresetFormModel(BaseModel):
    name: str
    workout_type: str

    @field_validator('name', mode='before')
    @classmethod
    def name_strip(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.strip()
        return v
