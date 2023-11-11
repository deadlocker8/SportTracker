import logging
from dataclasses import dataclass
from datetime import datetime, date

from dateutil.relativedelta import relativedelta
from flask import Blueprint, render_template
from flask_login import login_required, current_user

from blueprints.MonthGoals import get_month_goal_summary, MonthGoalDistanceFormModel, MonthGoalDistanceSummary
from logic import Constants
from logic.model.Models import Track, User, get_tracks_by_year_and_month, MonthGoalDistance

LOGGER = logging.getLogger(Constants.APP_NAME)


@dataclass
class MonthModel:
    name: str
    tracks: list[Track]
    goals: list[MonthGoalDistanceSummary]


def construct_blueprint():
    tracks = Blueprint('tracks', __name__, static_folder='static', url_prefix='/tracks')

    @tracks.route('/', defaults={'year': None, 'month': None})
    @tracks.route('/<int:year>/<int:month>')
    @login_required
    def listTracks(year: int, month: int):
        if year is None or month is None:
            monthRightSideDate = datetime.now().date()
        else:
            monthRightSideDate = date(year=year, month=month, day=1)

        monthRightSide = MonthModel(monthRightSideDate.strftime('%B %Y'),
                                    get_tracks_by_year_and_month(monthRightSideDate.year, monthRightSideDate.month),
                                    __get_goal_summaries(monthRightSideDate))

        monthLeftSideDate = monthRightSideDate - relativedelta(months=1)
        monthLeftSide = MonthModel(monthLeftSideDate.strftime('%B %Y'),
                                   get_tracks_by_year_and_month(monthLeftSideDate.year, monthLeftSideDate.month),
                                   __get_goal_summaries(monthLeftSideDate))

        nextMonthDate = monthRightSideDate + relativedelta(months=1)

        return render_template('tracks.jinja2',
                               monthLeftSide=monthLeftSide,
                               monthRightSide=monthRightSide,
                               previousMonthDate=monthLeftSideDate,
                               nextMonthDate=nextMonthDate,
                               currentMonthDate=datetime.now().date())

    def __get_goal_summaries(dateObject: date) -> list[MonthGoalDistanceSummary]:
        goals = (MonthGoalDistance.query.join(User)
                 .filter(User.username == current_user.username)
                 .filter(MonthGoalDistance.year == dateObject.year)
                 .filter(MonthGoalDistance.month == dateObject.month)
                 .all())

        if not goals:
            return []

        return [get_month_goal_summary(goal) for goal in goals]

    @tracks.route('/add')
    @login_required
    def add():
        return render_template('trackChooser.jinja2')

    return tracks
