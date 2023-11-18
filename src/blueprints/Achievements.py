import logging
from datetime import datetime

from flask import Blueprint, render_template
from flask_babel import gettext
from flask_login import login_required, current_user
from sqlalchemy import func, asc

from logic import Constants
from logic.model.Models import BikingTrack, db, RunningTrack, get_distance_per_month_by_type, \
    get_goal_summaries_by_year_and_month

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint():
    achievements = Blueprint('achievements', __name__, static_folder='static', url_prefix='/achievements')

    @achievements.route('/')
    @login_required
    def showAchievements():
        return render_template('achievements.jinja2',
                               bikingLongestTrack=__get_longest_distance_by_type(BikingTrack) / 1000,
                               bikingTotalDistance=__get_total_distance_by_type(BikingTrack) / 1000,
                               bikingBestMonth=__get_best_month_by_type(BikingTrack),
                               bikingStreak=__get_streaks_by_type(BikingTrack),
                               runningLongestTrack=__get_longest_distance_by_type(RunningTrack) / 1000,
                               runningTotalDistance=__get_total_distance_by_type(RunningTrack) / 1000,
                               runningBestMonth=__get_best_month_by_type(RunningTrack),
                               runningStreak=__get_streaks_by_type(RunningTrack),
                               )

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
        month = datetime.strptime(f'{int(bestMonth[1])}-{str(int(bestMonth[2])).zfill(2)}', '%Y-%m')
        return month.strftime('%B %Y'), float(bestMonth[0])

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
