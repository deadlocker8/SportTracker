import logging
from datetime import datetime, date

from flask import Blueprint, render_template
from flask_babel import gettext
from flask_login import login_required, current_user
from sqlalchemy import func, asc

from logic import Constants
from logic.model.Models import BikingTrack, db, RunningTrack, get_distance_per_month_by_type, \
    get_goal_summaries_by_year_and_month, Achievement

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint():
    achievements = Blueprint('achievements', __name__, static_folder='static', url_prefix='/achievements')

    @achievements.route('/')
    @login_required
    def showAchievements():
        return render_template('achievements.jinja2',
                               bikingAchievements=__get_biking_achievements(),
                               runningAchievements=__get_running_achievements(), )

    def __get_biking_achievements() -> list[Achievement]:
        bikingAchievements = []

        streak = __get_streaks_by_type(BikingTrack)
        bikingAchievements.append(Achievement(icon='sports_score',
                                              color='border-warning',
                                              title=gettext('Month Goal Streak'),
                                              description=gettext('You have achieved all your monthly goals for '
                                                                  '<span class="fw-bold">{currentStreak}</span> '
                                                                  'months in a row!<br>(Best: <span class="fw-bold">'
                                                                  '{maxStreak}</span>)').format(
                                                  currentStreak=streak[1], maxStreak=streak[0])))
        bikingAchievements.append(Achievement(icon='route',
                                              color='border-warning',
                                              title=gettext('Longest Track'),
                                              description=gettext('You cycled <span class="fw-bold">{longestTrack} km'
                                                                  '</span> in one trip!').format(
                                                  longestTrack=__get_longest_distance_by_type(BikingTrack) / 1000)))
        bikingAchievements.append(Achievement(icon='map',
                                              color='border-warning',
                                              title=gettext('Total Distance'),
                                              description=gettext('You cycled a total of <span class="fw-bold">'
                                                                  '{totalDistance} km</span>!').format(
                                                  totalDistance=__get_total_distance_by_type(BikingTrack) / 1000)))
        bestMonth = __get_best_month_by_type(BikingTrack)
        bikingAchievements.append(Achievement(icon='calendar_month',
                                              color='border-warning',
                                              title=gettext('Best Month'),
                                              description=gettext('<span class="fw-bold">{bestMonthName}</span> was '
                                                                  'your best month with <span class="fw-bold">'
                                                                  '{bestMonthDistance} km</span>!').format(
                                                  bestMonthName=bestMonth[0],
                                                  bestMonthDistance=bestMonth[1])))
        return bikingAchievements

    def __get_running_achievements() -> list[Achievement]:
        runningAchievements = []

        streak = __get_streaks_by_type(RunningTrack)
        runningAchievements.append(Achievement(icon='sports_score',
                                               color='border-info',
                                               title=gettext('Month Goal Streak'),
                                               description=gettext('You have achieved all your monthly goals for '
                                                                   '<span class="fw-bold">{currentStreak}</span> '
                                                                   'months in a row!<br>(Best: <span class="fw-bold">'
                                                                   '{maxStreak}</span>)').format(
                                                   currentStreak=streak[1], maxStreak=streak[0])))
        runningAchievements.append(Achievement(icon='route',
                                               color='border-info',
                                               title=gettext('Longest Track'),
                                               description=gettext('You ran <span class="fw-bold">{longestTrack} km'
                                                                   '</span> in one trip!').format(
                                                   longestTrack=__get_longest_distance_by_type(RunningTrack) / 1000)))
        runningAchievements.append(Achievement(icon='map',
                                               color='border-info',
                                               title=gettext('Total Distance'),
                                               description=gettext('You ran a total of <span class="fw-bold">'
                                                                   '{totalDistance} km</span>!').format(
                                                   totalDistance=__get_total_distance_by_type(RunningTrack) / 1000)))
        bestMonth = __get_best_month_by_type(RunningTrack)
        runningAchievements.append(Achievement(icon='calendar_month',
                                               color='border-info',
                                               title=gettext('Best Month'),
                                               description=gettext('<span class="fw-bold">{bestMonthName}</span> was '
                                                                   'your best month with <span class="fw-bold">'
                                                                   '{bestMonthDistance} km</span>!').format(
                                                   bestMonthName=bestMonth[0],
                                                   bestMonthDistance=bestMonth[1])))
        return runningAchievements

    def __get_longest_distance_by_type(trackClass) -> int:
        return (db.session.query(func.max(trackClass.distance))
                .filter(trackClass.user_id == current_user.id)
                .scalar() or 0)

    def __get_total_distance_by_type(trackClass) -> int:
        return (db.session.query(func.sum(trackClass.distance))
                .filter(trackClass.user_id == current_user.id)
                .scalar() or 0)

    def __get_best_month_by_type(trackClass) -> tuple[str, float]:
        rows = get_distance_per_month_by_type(trackClass)

        if not rows:
            return gettext('No month'), 0

        bestMonth = max(rows, key=lambda row: row[0])
        bestMonthDate = date(year=int(bestMonth[1]), month=int(bestMonth[2]), day=1)
        return bestMonthDate.strftime('%B %Y'), float(bestMonth[0])

    def __get_streaks_by_type(trackClass) -> tuple[int, int]:
        firstTrack = (trackClass.query
                      .filter(trackClass.user_id == current_user.id)
                      .order_by(asc(trackClass.startTime)).first())
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
