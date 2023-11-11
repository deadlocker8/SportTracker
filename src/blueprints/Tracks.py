import logging
from dataclasses import dataclass
from datetime import datetime, date

from dateutil.relativedelta import relativedelta
from flask import Blueprint, render_template
from flask_login import login_required

from logic import Constants
from logic.model.Models import Track, get_tracks_by_year_and_month, get_goal_summaries_by_year_and_month, \
    MonthGoalSummary

LOGGER = logging.getLogger(Constants.APP_NAME)


@dataclass
class MonthModel:
    name: str
    tracks: list[Track]
    goals: list[MonthGoalSummary]


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
                                    get_goal_summaries_by_year_and_month(monthRightSideDate.year,
                                                                         monthRightSideDate.month))

        monthLeftSideDate = monthRightSideDate - relativedelta(months=1)
        monthLeftSide = MonthModel(monthLeftSideDate.strftime('%B %Y'),
                                   get_tracks_by_year_and_month(monthLeftSideDate.year, monthLeftSideDate.month),
                                   get_goal_summaries_by_year_and_month(monthLeftSideDate.year,
                                                                        monthLeftSideDate.month))

        nextMonthDate = monthRightSideDate + relativedelta(months=1)

        return render_template('tracks.jinja2',
                               monthLeftSide=monthLeftSide,
                               monthRightSide=monthRightSide,
                               previousMonthDate=monthLeftSideDate,
                               nextMonthDate=nextMonthDate,
                               currentMonthDate=datetime.now().date())

    @tracks.route('/add')
    @login_required
    def add():
        return render_template('trackChooser.jinja2')

    return tracks
