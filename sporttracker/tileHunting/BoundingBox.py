from pydantic.dataclasses import dataclass


@dataclass
class BoundingBox:
    x_min: int
    x_max: int
    y_min: int
    y_max: int
