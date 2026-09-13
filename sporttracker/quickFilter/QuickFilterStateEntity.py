from __future__ import annotations

from datetime import date

from sqlalchemy import JSON, Date
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column

from sporttracker.db import db
from sporttracker.workout.WorkoutService import WorkoutService
from sporttracker.workout.WorkoutType import WorkoutType


class QuickFilterState(db.Model):  # type: ignore[name-defined]
    __tablename__ = 'filter_state_quick'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, primary_key=True)
    workout_types = db.Column(MutableDict.as_mutable(JSON))  # type: ignore[arg-type]
    years = db.Column(MutableDict.as_mutable(JSON))  # type: ignore[arg-type]
    date_from: Mapped[Date] = mapped_column(Date, nullable=True)
    date_to: Mapped[Date] = mapped_column(Date, nullable=True)

    def __repr__(self):
        return (
            f'QuickFilterState('
            f'user_id: {self.user_id}, '
            f'workout_types: {self.workout_types}, '
            f'years: {self.years}, '
            f'date_from: {self.date_from}, '
            f'date_to: {self.date_to})'
        )

    def get_workout_types(self) -> dict[WorkoutType, bool]:
        workoutTypes = {}
        for workoutTypeName, isActive in self.workout_types.items():
            try:
                workoutType = WorkoutType(workoutTypeName)  # type: ignore[call-arg]
                workoutTypes[workoutType] = isActive
            except ValueError:
                pass

        return workoutTypes

    def get_active_workout_types(self) -> list[WorkoutType]:
        return [workoutType for workoutType, isActive in self.get_workout_types().items() if isActive]

    def get_active_distance_workout_types(self) -> list[WorkoutType]:
        return [
            workoutType
            for workoutType in self.get_active_workout_types()
            if workoutType in WorkoutType.get_distance_workout_types()
        ]

    def get_years(self) -> dict[int, bool]:
        return {int(year): isActive for year, isActive in self.years.items()}

    def get_active_years(self) -> list[int]:
        return sorted([int(year) for year, isActive in self.get_years().items() if isActive])

    def is_all_years_active(self) -> bool:
        return all(self.years.values())

    def get_date_range(self) -> tuple[date, date] | None:
        if self.date_from is None or self.date_to is None:
            return None

        return self.date_from, self.date_to  # type: ignore[return-value]

    def is_date_filter_active(self) -> bool:
        return self.get_date_range() is not None

    def set_date_filter(self, date_from: date, date_to: date) -> None:
        self.date_from = date_from  # type: ignore[assignment]
        self.date_to = date_to  # type: ignore[assignment]

    def clear_date_filter(self) -> None:
        self.date_from = None  # type: ignore[assignment]
        self.date_to = None  # type: ignore[assignment]

    def get_effective_date_ranges(self) -> list[tuple[date, date]] | None:
        dateRange = self.get_date_range()
        if dateRange is not None:
            return [dateRange]

        if self.is_all_years_active():
            return None

        activeYears = self.get_active_years()
        if not activeYears:
            return []

        ranges = []
        rangeStartYear = rangeEndYear = activeYears[0]
        for year in activeYears[1:]:
            if year == rangeEndYear + 1:
                rangeEndYear = year
            else:
                ranges.append((date(rangeStartYear, 1, 1), date(rangeEndYear, 12, 31)))
                rangeStartYear = rangeEndYear = year

        ranges.append((date(rangeStartYear, 1, 1), date(rangeEndYear, 12, 31)))
        return ranges

    def is_any_filter_active(self) -> bool:
        if self.is_date_filter_active():
            return True

        return not self.is_all_years_active()

    def update(
        self,
        workout_types: dict[WorkoutType, bool],
        active_years: list[int],
    ):
        self.workout_types = {enumValue.name: isActive for enumValue, isActive in workout_types.items()}

        if self.years is None:
            self.years = {str(year): True for year in active_years}

        for year in self.years:
            self.years[year] = int(year) in active_years

    def reset(self, available_years: list[int]) -> QuickFilterState:
        self.update({workoutType: True for workoutType in WorkoutType}, available_years)
        return self

    def toggle_workout_type(self, workoutType: WorkoutType) -> None:
        self.workout_types[workoutType.name] = not self.workout_types[workoutType.name]

    def enable_all_workout_types(self) -> None:
        self.update({workoutType: True for workoutType in WorkoutType}, self.get_active_years())

    def update_missing_values(self, available_years: list[int]) -> bool:
        filterWorkoutTypes = self.get_workout_types()

        isUpdated = False
        for workoutType in [t for t in WorkoutType]:
            if workoutType not in filterWorkoutTypes:
                self.workout_types[workoutType.name] = True
                isUpdated = True

        if self.years is None:
            self.years = {}

        for year in available_years:
            if str(year) not in self.years:
                self.years[str(year)] = True
                isUpdated = True

        for year in list(self.years.keys()):
            if int(year) not in available_years:
                del self.years[year]
                isUpdated = True

        return isUpdated


def get_quick_filter_state_by_user(user_id: int) -> QuickFilterState:
    quickFilterState = QuickFilterState.query.filter(QuickFilterState.user_id == user_id).first()
    if quickFilterState.update_missing_values(WorkoutService.get_available_years(user_id)):
        db.session.commit()

    return quickFilterState
