from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import date

from sporttracker.workout.WorkoutType import WorkoutType


@dataclass
class CacheCalculationTime:
    cacheName: str
    userId: int
    workoutTypes: list[WorkoutType]
    dateRanges: list[tuple[date, date]] | None
    durationSeconds: float

    def build_key(self) -> str:
        if self.dateRanges is None:
            activeDateRanges = 'NONE'
        else:
            activeDateRanges = '_'.join([f'{dateFrom}_{dateTo}' for dateFrom, dateTo in self.dateRanges])

        activeTypes = '_'.join(sorted([t.name for t in self.workoutTypes]))
        return f'{self.cacheName}_{self.userId}_{activeTypes}_{activeDateRanges}'


class LoadStatisticsCollector:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cacheCalculationTimes: dict[str, CacheCalculationTime] = {}

    def record_cache_calculation(
        self,
        cacheName: str,
        userId: int,
        workoutTypes: list[WorkoutType],
        dateRanges: list[tuple[date, date]] | None,
        durationSeconds: float,
    ) -> None:
        cacheCalculationTime = CacheCalculationTime(
            cacheName=cacheName,
            userId=userId,
            workoutTypes=list(workoutTypes),
            dateRanges=list(dateRanges) if dateRanges is not None else None,
            durationSeconds=durationSeconds,
        )

        with self._lock:
            self._cacheCalculationTimes[cacheCalculationTime.build_key()] = cacheCalculationTime

    def get_cache_calculation_times(self) -> list[CacheCalculationTime]:
        with self._lock:
            return list(self._cacheCalculationTimes.values())

    def invalidate_cache_entry_by_user(self, cacheName: str, userId: int) -> None:
        keyPrefix = f'{cacheName}_{userId}_'

        with self._lock:
            for key in list(self._cacheCalculationTimes.keys()):
                if key.startswith(keyPrefix):
                    del self._cacheCalculationTimes[key]
