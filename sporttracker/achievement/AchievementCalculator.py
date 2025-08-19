from datetime import datetime, date
from statistics import mean

from flask_login import current_user
from sqlalchemy import asc, func, extract

from sporttracker.achievement.AchievementEntity import (
    LongestWorkoutDistanceAchievementHistoryItem,
    LongestWorkoutDurationAchievementHistoryItem,
    BestMonthDistanceAchievementHistoryItem,
    BestMonthDurationAchievementHistoryItem,
)
from sporttracker.workout.distance.DistanceWorkoutEntity import (
    get_distance_per_month_by_type,
    DistanceWorkout,
)
from sporttracker.monthGoal.MonthGoalEntity import get_goal_summaries_by_year_and_month_and_types
from sporttracker.workout.WorkoutEntity import Workout, get_duration_per_month_by_type
from sporttracker.workout.WorkoutType import WorkoutType
from sporttracker.logic.model.db import db


class AchievementCalculator:
    BEST_MONTH_HISTORY_SIZE = 5
    LONGEST_WORKOUT_HISTORY_SIZE = 5

    @staticmethod
    def get_workouts_with_longest_distances_by_type(
        workoutType: WorkoutType,
    ) -> list[LongestWorkoutDistanceAchievementHistoryItem]:
        longestWorkouts = (
            DistanceWorkout.query.filter(DistanceWorkout.type == workoutType)
            .filter(DistanceWorkout.user_id == current_user.id)
            .order_by(DistanceWorkout.distance.desc())
            .limit(AchievementCalculator.LONGEST_WORKOUT_HISTORY_SIZE)
            .all()
        )

        historyItems = []
        for workout in longestWorkouts:
            historyItems.append(
                LongestWorkoutDistanceAchievementHistoryItem(workout.start_time, workout.distance / 1000, workout.id)
            )

        return historyItems

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
    def get_best_distance_months_by_type(workoutType: WorkoutType) -> list[BestMonthDistanceAchievementHistoryItem]:
        maxDate, minDate = AchievementCalculator._get_min_and_max_date(workoutType)

        if minDate is None or maxDate is None:
            return [BestMonthDistanceAchievementHistoryItem.get_dummy_instance()]

        monthDistanceSums = get_distance_per_month_by_type(workoutType, minDate.year, maxDate.year)
        monthDistanceSums = [month for month in monthDistanceSums if month.distanceSum > 0.0]

        if not monthDistanceSums:
            return [BestMonthDistanceAchievementHistoryItem.get_dummy_instance()]

        bestMonths = sorted(monthDistanceSums, key=lambda monthDistanceSum: monthDistanceSum.distanceSum, reverse=True)

        result = []
        for month in bestMonths[: AchievementCalculator.BEST_MONTH_HISTORY_SIZE]:
            bestMonthDate = date(year=month.year, month=month.month, day=1)
            result.append(BestMonthDistanceAchievementHistoryItem(bestMonthDate, month.distanceSum))

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
    def get_workouts_with_longest_durations_by_type(
        workoutType: WorkoutType,
    ) -> list[LongestWorkoutDurationAchievementHistoryItem]:
        longestWorkouts = (
            Workout.query.filter(Workout.type == workoutType)
            .filter(Workout.user_id == current_user.id)
            .order_by(Workout.duration.desc())
            .limit(AchievementCalculator.LONGEST_WORKOUT_HISTORY_SIZE)
            .all()
        )

        historyItems = []
        for workout in longestWorkouts:
            historyItems.append(
                LongestWorkoutDurationAchievementHistoryItem(
                    workout.start_time, workout.duration, workout.id, workout.type
                )
            )

        return historyItems

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
    def get_best_duration_month_by_type(workoutType: WorkoutType) -> list[BestMonthDurationAchievementHistoryItem]:
        maxDate, minDate = AchievementCalculator._get_min_and_max_date(workoutType)

        if minDate is None or maxDate is None:
            return [BestMonthDurationAchievementHistoryItem.get_dummy_instance()]

        monthDurationSums = get_duration_per_month_by_type(workoutType, minDate.year, maxDate.year)
        monthDurationSums = [month for month in monthDurationSums if month.durationSum > 0.0]

        if not monthDurationSums:
            return [BestMonthDurationAchievementHistoryItem.get_dummy_instance()]

        bestMonths = sorted(monthDurationSums, key=lambda monthDistanceSum: monthDistanceSum.durationSum, reverse=True)

        result = []
        for month in bestMonths[: AchievementCalculator.BEST_MONTH_HISTORY_SIZE]:
            bestMonthDate = date(year=month.year, month=month.month, day=1)
            result.append(BestMonthDurationAchievementHistoryItem(bestMonthDate, month.durationSum))

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
