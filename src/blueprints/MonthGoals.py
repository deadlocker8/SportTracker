import logging

from flask import Blueprint, render_template
from flask_login import login_required, current_user

from logic import Constants
from logic.model.Models import User, MonthGoalDistance, MonthGoalCount

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint():
    monthGoals = Blueprint('monthGoals', __name__, static_folder='static', url_prefix='/goals')

    @monthGoals.route('/')
    @login_required
    def listMonthGoals():
        goalsDistance: list[MonthGoalDistance] = (MonthGoalDistance.query.join(User)
                                                  .filter(User.username == current_user.username)
                                                  .order_by(MonthGoalDistance.year.desc())
                                                  .order_by(MonthGoalDistance.month.desc())
                                                  .all())

        goalsCount: list[MonthGoalCount] = (MonthGoalCount.query.join(User)
                                            .filter(User.username == current_user.username)
                                            .order_by(MonthGoalCount.year.desc())
                                            .order_by(MonthGoalCount.month.desc())
                                            .all())

        goals = goalsDistance + goalsCount
        goals.sort(key=lambda summary: f'{summary.year}_{str(summary.month).zfill(2)}', reverse=True)

        goalSummaries = []
        for goal in goals:
            goalSummaries.append(goal.get_summary())

        return render_template('monthGoals.jinja2', monthGoalSummaries=goalSummaries)

    @monthGoals.route('/add')
    @login_required
    def add():
        return render_template('monthGoalChooser.jinja2')

    return monthGoals
