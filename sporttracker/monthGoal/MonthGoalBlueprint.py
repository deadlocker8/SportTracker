import logging
from datetime import datetime

from flask import Blueprint, render_template
from flask_login import current_user, login_required

from sporttracker import Constants
from sporttracker.monthGoal.MonthGoalEntity import MonthGoalCount, MonthGoalDistance, MonthGoalDuration
from sporttracker.monthGoal.MonthGoalService import MonthGoalService
from sporttracker.quickFilter.QuickFilterStateEntity import get_quick_filter_state_by_user
from sporttracker.user.UserEntity import User

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint():
    monthGoals = Blueprint('monthGoals', __name__, static_folder='static', url_prefix='/goals')

    @monthGoals.route('/', defaults={'year': None}, methods=['GET'])
    @monthGoals.route('/<int:year>', methods=['GET'])
    @login_required
    def listMonthGoals(year: int | None):
        if year is None:
            year = datetime.now().year

        quickFilterState = get_quick_filter_state_by_user(current_user.id)

        goalsDistance: list[MonthGoalDistance] = (
            MonthGoalDistance.query.join(User)
            .filter(User.username == current_user.username)
            .filter(MonthGoalDistance.year == year)
            .filter(MonthGoalDistance.type.in_(quickFilterState.get_active_workout_types()))
            .order_by(MonthGoalDistance.month.desc())
            .all()
        )

        goalsCount: list[MonthGoalCount] = (
            MonthGoalCount.query.join(User)
            .filter(User.username == current_user.username)
            .filter(MonthGoalCount.year == year)
            .filter(MonthGoalCount.type.in_(quickFilterState.get_active_workout_types()))
            .order_by(MonthGoalCount.month.desc())
            .all()
        )

        goalsDuration: list[MonthGoalDuration] = (
            MonthGoalDuration.query.join(User)
            .filter(User.username == current_user.username)
            .filter(MonthGoalDuration.year == year)
            .filter(MonthGoalDuration.type.in_(quickFilterState.get_active_workout_types()))
            .order_by(MonthGoalDuration.month.desc())
            .all()
        )

        goals = goalsDistance + goalsCount + goalsDuration
        goals.sort(key=lambda summary: f'{summary.year}_{str(summary.month).zfill(2)}', reverse=True)

        return render_template(
            'monthGoal/monthGoals.jinja2',
            goals=goals,
            selectedYear=year,
            availableYears=MonthGoalService.get_available_years(current_user.id),
            quickFilterState=quickFilterState,
        )

    @monthGoals.route('/add', methods=['GET'])
    @login_required
    def add():
        return render_template('monthGoal/monthGoalChooser.jinja2')

    return monthGoals
