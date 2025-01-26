from datetime import datetime, date
from statistics import mean

from flask_babel import format_datetime, gettext
from flask_login import current_user
from sqlalchemy import asc, func, extract

from sporttracker.logic.model.DistanceSport import (
    get_distance_per_month_by_type,
    DistanceSport,
)
from sporttracker.logic.model.MonthGoal import get_goal_summaries_by_year_and_month_and_types
from sporttracker.logic.model.Sport import Sport, get_duration_per_month_by_type
from sporttracker.logic.model.WorkoutType import WorkoutType
from sporttracker.logic.model.db import db


class AchievementCalculator:
    @staticmethod
    def get_sport_with_longest_distance_by_type(workoutType: WorkoutType) -> DistanceSport | None:
        return (
            DistanceSport.query.filter(DistanceSport.type == workoutType)
            .filter(DistanceSport.user_id == current_user.id)
            .order_by(DistanceSport.distance.desc())
            .first()
        )

    @staticmethod
    def get_longest_distance_by_type_and_year(workoutType: WorkoutType, year: int) -> float:
        value = (
            db.session.query(func.max(DistanceSport.distance))
            .filter(DistanceSport.type == workoutType)
            .filter(DistanceSport.user_id == current_user.id)
            .filter(extract('year', DistanceSport.start_time) == year)
            .scalar()
            or 0
        )
        return value / 1000

    @staticmethod
    def get_total_distance_by_type(workoutType: WorkoutType) -> float:
        value = (
            db.session.query(func.sum(DistanceSport.distance))
            .filter(DistanceSport.type == workoutType)
            .filter(DistanceSport.user_id == current_user.id)
            .scalar()
            or 0
        )
        return value / 1000

    @staticmethod
    def get_total_distance_by_type_and_year(workoutType: WorkoutType, year: int) -> float:
        value = (
            db.session.query(func.sum(DistanceSport.distance))
            .filter(DistanceSport.type == workoutType)
            .filter(DistanceSport.user_id == current_user.id)
            .filter(extract('year', DistanceSport.start_time) == year)
            .scalar()
            or 0
        )
        return value / 1000

    @staticmethod
    def get_best_distance_month_by_type(workoutType: WorkoutType) -> tuple[str, float]:
        maxDate, minDate = AchievementCalculator._get_min_and_max_date(workoutType)

        if minDate is None or maxDate is None:
            return gettext('No month'), 0

        monthDistanceSums = get_distance_per_month_by_type(workoutType, minDate.year, maxDate.year)

        if not monthDistanceSums:
            return gettext('No month'), 0

        bestMonth = max(
            monthDistanceSums, key=lambda monthDistanceSum: monthDistanceSum.distanceSum
        )
        bestMonthDate = date(year=bestMonth.year, month=bestMonth.month, day=1)
        return format_datetime(bestMonthDate, format='MMMM yyyy'), bestMonth.distanceSum

    @staticmethod
    def get_streaks_by_type(workoutType: WorkoutType, currentDate: date) -> tuple[int, int]:
        firstSport = AchievementCalculator._get_first_sport(workoutType)
        if firstSport is None:
            return 0, 0

        currentYear = currentDate.year
        currentMonth = currentDate.month

        year = firstSport.start_time.year  # type: ignore[attr-defined]
        month = firstSport.start_time.month  # type: ignore[attr-defined]

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
    def get_sport_with_longest_duration_by_type(workoutType: WorkoutType) -> Sport | None:
        return (
            Sport.query.filter(Sport.type == workoutType)
            .filter(Sport.user_id == current_user.id)
            .order_by(Sport.duration.desc())
            .first()
        )

    @staticmethod
    def get_longest_duration_by_type_and_year(workoutType: WorkoutType, year: int) -> int:
        value = (
            db.session.query(func.max(Sport.duration))
            .filter(Sport.type == workoutType)
            .filter(Sport.user_id == current_user.id)
            .filter(extract('year', Sport.start_time) == year)
            .scalar()
            or 0
        )
        return value

    @staticmethod
    def get_total_duration_by_type(workoutType: WorkoutType) -> int:
        value = (
            db.session.query(func.sum(Sport.duration))
            .filter(Sport.type == workoutType)
            .filter(Sport.user_id == current_user.id)
            .scalar()
            or 0
        )
        return value

    @staticmethod
    def get_best_duration_month_by_type(workoutType: WorkoutType) -> tuple[str, int]:
        maxDate, minDate = AchievementCalculator._get_min_and_max_date(workoutType)

        if minDate is None or maxDate is None:
            return gettext('No month'), 0

        monthDurationSums = get_duration_per_month_by_type(workoutType, minDate.year, maxDate.year)

        if not monthDurationSums:
            return gettext('No month'), 0

        bestMonth = max(
            monthDurationSums, key=lambda monthDurationSum: monthDurationSum.durationSum
        )
        bestMonthDate = date(year=bestMonth.year, month=bestMonth.month, day=1)
        return format_datetime(bestMonthDate, format='MMMM yyyy'), bestMonth.durationSum

    @staticmethod
    def _get_min_and_max_date(workoutType: WorkoutType) -> tuple[datetime | None, datetime | None]:
        result = db.session.query(
            func.min(Sport.start_time),
            func.max(Sport.start_time)
            .filter(Sport.type == workoutType)
            .filter(Sport.user_id == current_user.id),
        ).first()
        if result is None:
            return None, None

        minDate, maxDate = result
        return maxDate, minDate

    @staticmethod
    def _get_first_sport(workoutType: WorkoutType) -> Sport | None:
        return (
            Sport.query.filter(Sport.type == workoutType)
            .filter(Sport.user_id == current_user.id)
            .order_by(asc(Sport.start_time))
            .first()
        )

    @staticmethod
    def get_total_duration_by_type_and_year(workoutType: WorkoutType, year: int) -> int:
        value = (
            db.session.query(func.sum(Sport.duration))
            .filter(Sport.type == workoutType)
            .filter(Sport.user_id == current_user.id)
            .filter(extract('year', Sport.start_time) == year)
            .scalar()
            or 0
        )
        return value

    @staticmethod
    def get_total_number_of_sports_by_type_and_year(workoutType: WorkoutType, year: int) -> int:
        return (
            Sport.query.filter(Sport.type == workoutType)
            .filter(Sport.user_id == current_user.id)
            .filter(extract('year', Sport.start_time) == year)
            .count()
        )

    @staticmethod
    def get_average_speed_by_type_and_year(workoutType: WorkoutType, year: int) -> float:
        sports = (
            DistanceSport.query.filter(DistanceSport.user_id == current_user.id)
            .filter(DistanceSport.type == workoutType)
            .filter(extract('year', DistanceSport.start_time) == year)
            .all()
        )

        speedData = [
            sport.distance / sport.duration * 3.6 for sport in sports if sport.duration is not None
        ]
        return round(mean(speedData), 2) if speedData else 0.0
