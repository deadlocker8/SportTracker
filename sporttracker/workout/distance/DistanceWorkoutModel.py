from pydantic import ConfigDict, field_validator

from sporttracker.workout.WorkoutModel import BaseWorkoutFormModel


class DistanceWorkoutFormModel(BaseWorkoutFormModel):
    distance: float
    planned_tour_id: str = '-1'
    elevation_sum: int | None = None
    gpx_file_name: str | None = None
    has_fit_file: bool = False
    share_code: str | None = None
    fit_file_name: str | None = None  # only used during import from FIT file

    model_config = ConfigDict(
        extra='allow',
    )

    @field_validator(*['elevation_sum'], mode='before')
    def elevationSumCheck(cls, value: str, info) -> str | None:
        if isinstance(value, str):
            value = value.strip()
        if value == '':
            return None
        return value
