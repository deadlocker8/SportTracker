import logging

from flask import Blueprint, render_template
from flask_login import login_required, current_user

from sporttracker.logic import Constants
from sporttracker.logic.model.MonthGoal import MonthGoalDistance, MonthGoalCount, MonthGoalSummary
from sporttracker.logic.model.User import User

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint():
    monthGoals = Blueprint('monthGoals', __name__, static_folder='static', url_prefix='/goals')

    @monthGoals.route('/')
    @login_required
    def listMonthGoals():
        goalsDistance: list[MonthGoalDistance] = (
            MonthGoalDistance.query.join(User)
            .filter(User.username == current_user.username)
            .order_by(MonthGoalDistance.year.desc())
            .order_by(MonthGoalDistance.month.desc())
            .all()
        )

        goalsCount: list[MonthGoalCount] = (
            MonthGoalCount.query.join(User)
            .filter(User.username == current_user.username)
            .order_by(MonthGoalCount.year.desc())
            .order_by(MonthGoalCount.month.desc())
            .all()
        )

        goals = goalsDistance + goalsCount
        goals.sort(
            key=lambda summary: f'{summary.year}_{str(summary.month).zfill(2)}', reverse=True
        )

        currentYear = None
        summariesByYear = {}
        summaries: list[MonthGoalSummary] = []
        for goal in goals:
            if currentYear is None:
                currentYear = goal.year

            if goal.year != currentYear:
                summariesByYear[currentYear] = summaries
                currentYear = goal.year
                summaries = []

            summaries.append(goal.get_summary())

        if currentYear is not None:
            summariesByYear[currentYear] = summaries

        return render_template(
            'monthGoals/monthGoals.jinja2', monthGoalSummariesByYear=summariesByYear
        )

    @monthGoals.route('/add')
    @login_required
    def add():
        return render_template('monthGoals/monthGoalChooser.jinja2')

    return monthGoals
