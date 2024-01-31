from datetime import datetime, date

from flask_babel import format_datetime, gettext
from flask_login import current_user
from sqlalchemy import asc, func

from logic.model.MonthGoal import get_goal_summaries_by_year_and_month_and_types
from logic.model.Track import get_distance_per_month_by_type, TrackType, Track
from logic.model.db import db


class AchievementCalculator:
    @staticmethod
    def get_longest_distance_by_type(trackType: TrackType) -> float:
        value = (db.session.query(func.max(Track.distance))
                 .filter(Track.type == trackType)
                 .filter(Track.user_id == current_user.id)
                 .scalar() or 0)
        return value / 1000

    @staticmethod
    def get_total_distance_by_type(trackType: TrackType) -> float:
        value = (db.session.query(func.sum(Track.distance))
                 .filter(Track.type == trackType)
                 .filter(Track.user_id == current_user.id)
                 .scalar() or 0)
        return value / 1000

    @staticmethod
    def get_best_month_by_type(trackType: TrackType) -> tuple[str, float]:
        maxDate, minDate = AchievementCalculator._get_min_and_max_date(trackType)

        if minDate is None or maxDate is None:
            return gettext('No month'), 0

        monthDistanceSums = get_distance_per_month_by_type(trackType, minDate.year, maxDate.year)

        if not monthDistanceSums:
            return gettext('No month'), 0

        bestMonth = max(monthDistanceSums, key=lambda monthDistanceSum: monthDistanceSum.distanceSum)
        bestMonthDate = date(year=bestMonth.year, month=bestMonth.month, day=1)
        return format_datetime(bestMonthDate, format='MMMM yyyy'), bestMonth.distanceSum

    @staticmethod
    def get_streaks_by_type(trackType: TrackType) -> tuple[int, int]:
        firstTrack = AchievementCalculator._get_first_track(trackType)
        if firstTrack is None:
            return 0, 0

        now = datetime.now()
        currentYear = now.year
        currentMonth = now.month

        year = firstTrack.startTime.year
        month = firstTrack.startTime.month

        highestStreak = 0
        currentStreak = 0

        while True:
            summaries = get_goal_summaries_by_year_and_month_and_types(year, month, [trackType])
            completedGoals = [s for s in summaries if s.percentage >= 100.0]
            if summaries and len(summaries) == len(completedGoals):
                currentStreak += 1
                if currentStreak > highestStreak:
                    highestStreak = currentStreak
            else:
                currentStreak = 0

            if year == currentYear and month == currentMonth:
                break

            month += 1
            if month > 12:
                month = 1
                year += 1

        return highestStreak, currentStreak

    @staticmethod
    def _get_min_and_max_date(trackType: TrackType) -> tuple[datetime | None, datetime | None]:
        minDate, maxDate = (
            db.session.query(func.min(Track.startTime), func.max(Track.startTime)
                             .filter(Track.type == trackType)
                             .filter(Track.user_id == current_user.id))
            .first())
        return maxDate, minDate

    @staticmethod
    def _get_first_track(trackType: TrackType) -> Track | None:
        return (Track.query
                .filter(Track.type == trackType)
                .filter(Track.user_id == current_user.id)
                .order_by(asc(Track.startTime)).first())
