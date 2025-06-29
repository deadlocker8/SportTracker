from datetime import datetime, date
from statistics import mean

from flask_babel import format_datetime, gettext
from flask_login import current_user
from sqlalchemy import asc, func, extract

from sporttracker.logic.model.Achievement import DistanceAchievementHistoryItem, DurationAchievementHistoryItem
from sporttracker.logic.model.DistanceWorkout import (
    get_distance_per_month_by_type,
    DistanceWorkout,
)
from sporttracker.logic.model.MonthGoal import get_goal_summaries_by_year_and_month_and_types
from sporttracker.logic.model.Workout import Workout, get_duration_per_month_by_type
from sporttracker.logic.model.WorkoutType import WorkoutType
from sporttracker.logic.model.db import db


class AchievementCalculator:
    BEST_MONTH_HISTORY_SIZE = 5

    @staticmethod
    def get_workout_with_longest_distance_by_type(
        workoutType: WorkoutType,
    ) -> DistanceWorkout | None:
        return (
            DistanceWorkout.query.filter(DistanceWorkout.type == workoutType)
            .filter(DistanceWorkout.user_id == current_user.id)
            .order_by(DistanceWorkout.distance.desc())
            .first()
        )

    @staticmethod
    def get_longest_distance_by_type_and_year(workoutType: WorkoutType, year: int) -> float:
        value = (
            db.session.query(func.max(DistanceWorkout.distance))
            .filter(DistanceWorkout.type == workoutType)
            .filter(DistanceWorkout.user_id == current_user.id)
            .filter(extract('year', DistanceWorkout.start_time) == year)
            .scalar()
            or 0
        )
        return value / 1000

    @staticmethod
    def get_total_distance_by_type(workoutType: WorkoutType) -> float:
        value = (
            db.session.query(func.sum(DistanceWorkout.distance))
            .filter(DistanceWorkout.type == workoutType)
            .filter(DistanceWorkout.user_id == current_user.id)
            .scalar()
            or 0
        )
        return value / 1000

    @staticmethod
    def get_total_distance_by_type_and_year(workoutType: WorkoutType, year: int) -> float:
        value = (
            db.session.query(func.sum(DistanceWorkout.distance))
            .filter(DistanceWorkout.type == workoutType)
            .filter(DistanceWorkout.user_id == current_user.id)
            .filter(extract('year', DistanceWorkout.start_time) == year)
            .scalar()
            or 0
        )
        return value / 1000

    @staticmethod
    def get_best_distance_months_by_type(workoutType: WorkoutType) -> list[DistanceAchievementHistoryItem]:
        maxDate, minDate = AchievementCalculator._get_min_and_max_date(workoutType)

        if minDate is None or maxDate is None:
            return [DistanceAchievementHistoryItem(gettext('No month'), 0)]

        monthDistanceSums = get_distance_per_month_by_type(workoutType, minDate.year, maxDate.year)
        monthDistanceSums = [month for month in monthDistanceSums if month.distanceSum > 0.0]

        if not monthDistanceSums:
            return [DistanceAchievementHistoryItem(gettext('No month'), 0)]

        bestMonths = sorted(monthDistanceSums, key=lambda monthDistanceSum: monthDistanceSum.distanceSum, reverse=True)

        result = []
        for month in bestMonths[: AchievementCalculator.BEST_MONTH_HISTORY_SIZE]:
            bestMonthDate = date(year=month.year, month=month.month, day=1)
            result.append(
                DistanceAchievementHistoryItem(format_datetime(bestMonthDate, format='MMMM yyyy'), month.distanceSum)
            )

        return result

    @staticmethod
    def get_streaks_by_type(workoutType: WorkoutType, currentDate: date) -> tuple[int, int]:
        firstWorkout = AchievementCalculator._get_first_workout(workoutType)
        if firstWorkout is None:
            return 0, 0

        currentYear = currentDate.year
        currentMonth = currentDate.month

        year = firstWorkout.start_time.year  # type: ignore[attr-defined]
        month = firstWorkout.start_time.month  # type: ignore[attr-defined]

        highestStreak = 0
        currentStreak = 0

        isEndReached = False

        while not isEndReached:
            summaries = get_goal_summaries_by_year_and_month_and_types(year, month, [workoutType])
            completedGoals = [s for s in summaries if s.percentage >= 100.0]

            if year == currentYear and month == currentMonth:
                isEndReached = True

            if summaries and len(summaries) == len(completedGoals):
                currentStreak += 1
                if currentStreak > highestStreak:
                    highestStreak = currentStreak
            elif summaries:
                if not isEndReached:
                    currentStreak = 0

            month += 1
            if month > 12:
                month = 1
                year += 1

        return highestStreak, currentStreak

    @staticmethod
    def get_workout_with_longest_duration_by_type(workoutType: WorkoutType) -> Workout | None:
        return (
            Workout.query.filter(Workout.type == workoutType)
            .filter(Workout.user_id == current_user.id)
            .order_by(Workout.duration.desc())
            .first()
        )

    @staticmethod
    def get_longest_duration_by_type_and_year(workoutType: WorkoutType, year: int) -> int:
        value = (
            db.session.query(func.max(Workout.duration))
            .filter(Workout.type == workoutType)
            .filter(Workout.user_id == current_user.id)
            .filter(extract('year', Workout.start_time) == year)
            .scalar()
            or 0
        )
        return value

    @staticmethod
    def get_total_duration_by_type(workoutType: WorkoutType) -> int:
        value = (
            db.session.query(func.sum(Workout.duration))
            .filter(Workout.type == workoutType)
            .filter(Workout.user_id == current_user.id)
            .scalar()
            or 0
        )
        return value

    @staticmethod
    def get_best_duration_month_by_type(workoutType: WorkoutType) -> list[DurationAchievementHistoryItem]:
        maxDate, minDate = AchievementCalculator._get_min_and_max_date(workoutType)

        if minDate is None or maxDate is None:
            return [DurationAchievementHistoryItem(gettext('No month'), 0)]

        monthDurationSums = get_duration_per_month_by_type(workoutType, minDate.year, maxDate.year)
        monthDurationSums = [month for month in monthDurationSums if month.durationSum > 0.0]

        if not monthDurationSums:
            return [DurationAchievementHistoryItem(gettext('No month'), 0)]

        bestMonths = sorted(monthDurationSums, key=lambda monthDistanceSum: monthDistanceSum.durationSum, reverse=True)

        result = []
        for month in bestMonths[: AchievementCalculator.BEST_MONTH_HISTORY_SIZE]:
            bestMonthDate = date(year=month.year, month=month.month, day=1)
            result.append(
                DurationAchievementHistoryItem(format_datetime(bestMonthDate, format='MMMM yyyy'), month.durationSum)
            )

        return result

    @staticmethod
    def _get_min_and_max_date(workoutType: WorkoutType) -> tuple[datetime | None, datetime | None]:
        result = db.session.query(
            func.min(Workout.start_time),
            func.max(Workout.start_time).filter(Workout.type == workoutType).filter(Workout.user_id == current_user.id),
        ).first()
        if result is None:
            return None, None

        minDate, maxDate = result
        return maxDate, minDate

    @staticmethod
    def _get_first_workout(workoutType: WorkoutType) -> Workout | None:
        return (
            Workout.query.filter(Workout.type == workoutType)
            .filter(Workout.user_id == current_user.id)
            .order_by(asc(Workout.start_time))
            .first()
        )

    @staticmethod
    def get_total_duration_by_type_and_year(workoutType: WorkoutType, year: int) -> int:
        value = (
            db.session.query(func.sum(Workout.duration))
            .filter(Workout.type == workoutType)
            .filter(Workout.user_id == current_user.id)
            .filter(extract('year', Workout.start_time) == year)
            .scalar()
            or 0
        )
        return value

    @staticmethod
    def get_total_number_of_workouts_by_type_and_year(workoutType: WorkoutType, year: int) -> int:
        return (
            Workout.query.filter(Workout.type == workoutType)
            .filter(Workout.user_id == current_user.id)
            .filter(extract('year', Workout.start_time) == year)
            .count()
        )

    @staticmethod
    def get_average_speed_by_type_and_year(workoutType: WorkoutType, year: int) -> float:
        workouts = (
            DistanceWorkout.query.filter(DistanceWorkout.user_id == current_user.id)
            .filter(DistanceWorkout.type == workoutType)
            .filter(extract('year', DistanceWorkout.start_time) == year)
            .all()
        )

        speedData = [
            workout.distance / workout.duration * 3.6
            for workout in workouts
            if workout.duration is not None and workout.duration > 0
        ]
        return round(mean(speedData), 2) if speedData else 0.0
