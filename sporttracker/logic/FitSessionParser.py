from dataclasses import dataclass
from datetime import datetime

import fitdecode  # type: ignore[import-untyped]

from sporttracker.logic.model.WorkoutType import WorkoutType


@dataclass
class FitSession:
    start_time: datetime
    duration: int
    workout_type: WorkoutType
    distance: int | None
    total_ascent: int | None
    average_heart_rate: int | None


class FitSessionParser:
    @staticmethod
    def parse(fitFileContent: bytes) -> FitSession | None:
        with fitdecode.FitReader(fitFileContent) as fit_file:
            for frame in fit_file:
                if not isinstance(frame, fitdecode.records.FitDataMessage):
                    continue

                if frame.name != 'session':
                    continue

                distance = frame.get_value('total_distance', fallback=None)
                total_ascent = frame.get_value('total_ascent', fallback=None)
                average_heart_rate = frame.get_value('avg_heart_rate', fallback=None)

                return FitSession(
                    start_time=frame.get_value('start_time'),
                    duration=int(frame.get_value('total_timer_time')),
                    workout_type=FitSessionParser.__parse_sport(frame.get_value('sport')),
                    distance=None if distance is None else int(distance),
                    total_ascent=None if total_ascent is None else int(total_ascent),
                    average_heart_rate=None
                    if average_heart_rate is None
                    else int(average_heart_rate),
                )

        return None

    @staticmethod
    def __parse_sport(sport: str) -> WorkoutType:
        if sport.strip().lower() == 'cycling':
            return WorkoutType.BIKING
        elif sport.strip().lower() == 'running':
            return WorkoutType.RUNNING
        elif sport.strip().lower() in ['hiking', 'walking']:
            return WorkoutType.HIKING

        raise ValueError(f'Unsupported sport: "{sport}"')
