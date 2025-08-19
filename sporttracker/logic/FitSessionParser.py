from __future__ import annotations
import json
import os
from dataclasses import dataclass
from datetime import datetime, UTC

import fitdecode  # type: ignore[import-untyped]

from sporttracker.workout.WorkoutType import WorkoutType


@dataclass
class FitSession:
    file_name: str
    start_time: datetime
    duration: int
    workout_type: WorkoutType
    distance: int | None
    total_ascent: int | None
    average_heart_rate: int | None

    def to_json(self) -> str:
        return json.dumps(
            {
                'file_name': self.file_name,
                'start_time': self.start_time.strftime('%Y-%m-%d %H:%M:%S.%f'),
                'workout_type': self.workout_type.name,
                'duration': self.duration,
                'distance': self.distance,
                'total_ascent': self.total_ascent,
                'average_heart_rate': self.average_heart_rate,
            }
        )

    @staticmethod
    def from_json(json_string: str) -> FitSession:
        json_data = json.loads(json_string)
        return FitSession(
            file_name=json_data['file_name'],
            start_time=datetime.strptime(json_data['start_time'], '%Y-%m-%d %H:%M:%S.%f'),
            duration=json_data['duration'],
            workout_type=WorkoutType(json_data['workout_type']),  # type: ignore[call-arg]
            distance=json_data['distance'],
            total_ascent=json_data['total_ascent'],
            average_heart_rate=json_data['average_heart_rate'],
        )


class FitSessionParser:
    """
    Parses session information from a FIT file.
    Only the first session will be parsed.
    Only SportTracker relevant information will be parsed.
    The start time is converted to the local time zone.
    """

    @staticmethod
    def parse(fit_file_path: str) -> FitSession | None:
        with fitdecode.FitReader(fit_file_path) as fit_file:
            for frame in fit_file:
                if not isinstance(frame, fitdecode.records.FitDataMessage):
                    continue

                if frame.name != 'session':
                    continue

                start_time = frame.get_value('start_time').replace(tzinfo=UTC).astimezone()
                start_time = datetime(
                    year=start_time.year,
                    month=start_time.month,
                    day=start_time.day,
                    hour=start_time.hour,
                    minute=start_time.minute,
                    second=start_time.second,
                    microsecond=0,
                )
                distance = frame.get_value('total_distance', fallback=None)
                total_ascent = frame.get_value('total_ascent', fallback=None)
                average_heart_rate = frame.get_value('avg_heart_rate', fallback=None)

                return FitSession(
                    file_name=os.path.splitext(os.path.basename(fit_file_path))[0],
                    start_time=start_time,
                    duration=int(frame.get_value('total_timer_time')),
                    workout_type=FitSessionParser.__parse_sport(frame.get_value('sport')),
                    distance=None if distance is None else int(distance),
                    total_ascent=None if total_ascent is None else int(total_ascent),
                    average_heart_rate=None if average_heart_rate is None else int(average_heart_rate),
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
