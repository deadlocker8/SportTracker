import logging
from itertools import groupby

from flask import Blueprint, render_template
from flask_login import login_required, current_user

from sporttracker.logic import Constants
from sporttracker.logic.QuickFilterState import get_quick_filter_state_from_session
from sporttracker.logic.model.MonthGoal import MonthGoalDistance, MonthGoalCount, MonthGoalDuration
from sporttracker.logic.model.User import User

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint():
    monthGoals = Blueprint('monthGoals', __name__, static_folder='static', url_prefix='/goals')

    @monthGoals.route('/')
    @login_required
    def listMonthGoals():
        quickFilterState = get_quick_filter_state_from_session()

        goalsDistance: list[MonthGoalDistance] = (
            MonthGoalDistance.query.join(User)
            .filter(User.username == current_user.username)
            .filter(MonthGoalDistance.type.in_(quickFilterState.get_active_types()))
            .order_by(MonthGoalDistance.year.desc())
            .order_by(MonthGoalDistance.month.desc())
            .all()
        )

        goalsCount: list[MonthGoalCount] = (
            MonthGoalCount.query.join(User)
            .filter(User.username == current_user.username)
            .filter(MonthGoalCount.type.in_(quickFilterState.get_active_types()))
            .order_by(MonthGoalCount.year.desc())
            .order_by(MonthGoalCount.month.desc())
            .all()
        )

        goalsDuration: list[MonthGoalDuration] = (
            MonthGoalDuration.query.join(User)
            .filter(User.username == current_user.username)
            .filter(MonthGoalDuration.type.in_(quickFilterState.get_active_types()))
            .order_by(MonthGoalDuration.year.desc())
            .order_by(MonthGoalDuration.month.desc())
            .all()
        )

        goals = goalsDistance + goalsCount + goalsDuration
        goals.sort(key=lambda summary: f'{summary.year}_{str(summary.month).zfill(2)}', reverse=True)

        goalsByYear = {k: list(g) for k, g in groupby(goals, key=lambda goal: goal.year)}

        return render_template(
            'monthGoals/monthGoals.jinja2',
            goalsByYear=goalsByYear,
            quickFilterState=quickFilterState,
        )

    @monthGoals.route('/add')
    @login_required
    def add():
        return render_template('monthGoals/monthGoalChooser.jinja2')

    return monthGoals
