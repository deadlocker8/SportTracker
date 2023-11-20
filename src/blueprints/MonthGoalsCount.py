import logging

from flask import Blueprint, render_template, redirect, url_for, abort
from flask_login import login_required, current_user
from flask_pydantic import validate
from pydantic import BaseModel

from logic import Constants
from logic.model.Models import TrackType, db, MonthGoal, User, MonthGoalCount

LOGGER = logging.getLogger(Constants.APP_NAME)


class MonthGoalCountFormModel(BaseModel):
    type: str
    year: int
    month: int
    count_minimum: int
    count_perfect: int


def construct_blueprint():
    monthGoalsCount = Blueprint('monthGoalsCount', __name__, static_folder='static', url_prefix='/goalsCount')

    @monthGoalsCount.route('/add')
    @login_required
    def add():
        return render_template('monthGoalCountForm.jinja2')

    @monthGoalsCount.route('/post', methods=['POST'])
    @login_required
    @validate()
    def addPost(form: MonthGoalCountFormModel):
        monthGoal = MonthGoalCount(type=TrackType(form.type),
                                   year=form.year,
                                   month=form.month,
                                   count_minimum=form.count_minimum,
                                   count_perfect=form.count_perfect,
                                   user_id=current_user.id)
        LOGGER.debug(f'Saved new month goal of type "count": {monthGoal}')
        db.session.add(monthGoal)
        db.session.commit()

        return redirect(url_for('monthGoals.listMonthGoals'))

    @monthGoalsCount.route('/edit/<int:goal_id>')
    @login_required
    def edit(goal_id: int):
        monthGoal = (MonthGoalCount.query.join(User)
                     .filter(User.username == current_user.username)
                     .filter(MonthGoalCount.id == goal_id)
                     .first())

        if monthGoal is None:
            abort(404)

        goalModel = MonthGoalCountFormModel(type=monthGoal.type.name,
                                            year=monthGoal.year,
                                            month=monthGoal.month,
                                            count_minimum=monthGoal.count_minimum,
                                            count_perfect=monthGoal.count_perfect)

        return render_template('monthGoalCountForm.jinja2', goal=goalModel, goal_id=goal_id)

    @monthGoalsCount.route('/edit/<int:goal_id>', methods=['POST'])
    @login_required
    @validate()
    def editPost(goal_id: int, form: MonthGoalCountFormModel):
        monthGoal = (MonthGoalCount.query.join(User)
                     .filter(User.username == current_user.username)
                     .filter(MonthGoalCount.id == goal_id)
                     .first())

        if monthGoal is None:
            abort(404)

        monthGoal.type = TrackType(form.type)
        monthGoal.year = form.year
        monthGoal.month = form.month
        monthGoal.count_minimum = form.count_minimum
        monthGoal.count_perfect = form.count_perfect
        monthGoal.user_id = current_user.id

        LOGGER.debug(f'Updated month goal of type "count": {monthGoal}')
        db.session.commit()

        return redirect(url_for('monthGoals.listMonthGoals'))

    @monthGoalsCount.route('/delete/<int:goal_id>')
    @login_required
    def delete(goal_id: int):
        monthGoal = (MonthGoalCount.query.join(User)
                     .filter(User.username == current_user.username)
                     .filter(MonthGoalCount.id == goal_id)
                     .first())

        if monthGoal is None:
            abort(404)

        LOGGER.debug(f'Deleted month goal of type "count": {monthGoal}')
        db.session.delete(monthGoal)
        db.session.commit()

        return redirect(url_for('monthGoals.listMonthGoals'))

    return monthGoalsCount
