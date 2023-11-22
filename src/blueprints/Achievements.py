import logging
from datetime import datetime, date

from flask import Blueprint, render_template
from flask_babel import gettext
from flask_login import login_required, current_user
from sqlalchemy import func, asc

from logic import Constants
from logic.model.Models import db, get_distance_per_month_by_type, get_goal_summaries_by_year_and_month, Achievement, \
    TrackType, Track

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint():
    achievements = Blueprint('achievements', __name__, static_folder='static', url_prefix='/achievements')

    @achievements.route('/')
    @login_required
    def showAchievements():
        return render_template('achievements.jinja2', achievements=__get_achievements())

    def __get_achievements() -> dict[TrackType, list[Achievement]]:
        result = {}

        for trackType in TrackType:
            achievementList = []

            streak = __get_streaks_by_type(trackType)
            achievementList.append(Achievement(icon='sports_score',
                                               color=trackType.border_color,
                                               title=gettext('Month Goal Streak'),
                                               description=gettext('You have achieved all your monthly goals for '
                                                                   '<span class="fw-bold">{currentStreak}</span> '
                                                                   'months in a row!<br>(Best: <span class="fw-bold">'
                                                                   '{maxStreak}</span>)').format(
                                                   currentStreak=streak[1], maxStreak=streak[0])))
            achievementList.append(Achievement(icon='route',
                                               color=trackType.border_color,
                                               title=gettext('Longest Track'),
                                               description=gettext('You completed <span class="fw-bold">{longestTrack} '
                                                                   'km</span> in one trip!').format(
                                                   longestTrack=__get_longest_distance_by_type(trackType) / 1000)))
            achievementList.append(Achievement(icon='map',
                                               color=trackType.border_color,
                                               title=gettext('Total Distance'),
                                               description=gettext('You completed a total of <span class="fw-bold">'
                                                                   '{totalDistance} km</span>!').format(
                                                   totalDistance=__get_total_distance_by_type(trackType) / 1000)))
            bestMonth = __get_best_month_by_type(trackType)
            achievementList.append(Achievement(icon='calendar_month',
                                               color=trackType.border_color,
                                               title=gettext('Best Month'),
                                               description=gettext('<span class="fw-bold">{bestMonthName}</span> was '
                                                                   'your best month with <span class="fw-bold">'
                                                                   '{bestMonthDistance} km</span>!').format(
                                                   bestMonthName=bestMonth[0],
                                                   bestMonthDistance=bestMonth[1])))
            result[trackType] = achievementList
        return result

    def __get_longest_distance_by_type(trackType: TrackType) -> int:
        return (db.session.query(func.max(Track.distance))
                .filter(Track.type == trackType)
                .filter(Track.user_id == current_user.id)
                .scalar() or 0)

    def __get_total_distance_by_type(trackType: TrackType) -> int:
        return (db.session.query(func.sum(Track.distance))
                .filter(Track.type == trackType)
                .filter(Track.user_id == current_user.id)
                .scalar() or 0)

    def __get_best_month_by_type(trackType: TrackType) -> tuple[str, float]:
        minDate, maxDate = (
            db.session.query(func.min(Track.startTime), func.max(Track.startTime)
                             .filter(Track.type == trackType)
                             .filter(Track.user_id == current_user.id))
            .first())

        if minDate is None or maxDate is None:
            return gettext('No month'), 0

        monthDistanceSums = get_distance_per_month_by_type(trackType, minDate.year, maxDate.year)

        if not monthDistanceSums:
            return gettext('No month'), 0

        bestMonth = max(monthDistanceSums, key=lambda monthDistanceSum: monthDistanceSum.distanceSum)
        bestMonthDate = date(year=bestMonth.year, month=bestMonth.month, day=1)
        return bestMonthDate.strftime('%B %Y'), bestMonth.distanceSum

    def __get_streaks_by_type(trackType: TrackType) -> tuple[int, int]:
        firstTrack = (Track.query
                      .filter(Track.type == trackType)
                      .filter(Track.user_id == current_user.id)
                      .order_by(asc(Track.startTime)).first())
        if firstTrack is None:
            return 0, 0

        now = datetime.now()
        currentYear = now.year
        currentMonth = now.month

        year = firstTrack.startTime.year
        month = firstTrack.startTime.month

        highestStreak = 0
        currentStreak = 0

        while year != currentYear or month != currentMonth:
            summaries = get_goal_summaries_by_year_and_month(year, month)
            completedGoals = [s for s in summaries if s.percentage >= 100.0]
            if len(summaries) == len(completedGoals):
                currentStreak += 1
                if currentStreak > highestStreak:
                    highestStreak = currentStreak
            else:
                currentStreak = 0

            month += 1
            if month > 12:
                month = 1
                year += 1

        return highestStreak, currentStreak

    return achievements
