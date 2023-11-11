import logging

from flask import Blueprint, render_template, redirect, url_for, abort
from flask_login import login_required, current_user
from flask_pydantic import validate
from pydantic import BaseModel

from logic import Constants
from logic.model.Models import TrackType, db, MonthGoal, User, MonthGoalDistance

LOGGER = logging.getLogger(Constants.APP_NAME)


class MonthGoalDistanceFormModel(BaseModel):
    type: str
    year: int
    month: int
    distance_minimum: float
    distance_perfect: float


def construct_blueprint():
    monthGoalsDistance = Blueprint('monthGoalsDistance', __name__, static_folder='static', url_prefix='/goalsDistance')

    @monthGoalsDistance.route('/add')
    @login_required
    def add():
        return render_template('monthGoalDistanceForm.jinja2')

    @monthGoalsDistance.route('/post', methods=['POST'])
    @login_required
    @validate()
    def addPost(form: MonthGoalDistanceFormModel):
        monthGoal = MonthGoalDistance(type=TrackType(form.type),
                                      year=form.year,
                                      month=form.month,
                                      distance_minimum=form.distance_minimum * 1000,
                                      distance_perfect=form.distance_perfect * 1000,
                                      user_id=current_user.id)
        LOGGER.debug(f'Saved new month goal of type "distance": {monthGoal}')
        db.session.add(monthGoal)
        db.session.commit()

        return redirect(url_for('monthGoals.listMonthGoals'))

    @monthGoalsDistance.route('/edit/<int:goal_id>')
    @login_required
    def edit(goal_id: int):
        monthGoal = (MonthGoalDistance.query.join(User)
                     .filter(User.username == current_user.username)
                     .filter(MonthGoalDistance.id == goal_id)
                     .first())

        if monthGoal is None:
            abort(404)

        goalModel = MonthGoalDistanceFormModel(type=monthGoal.type.name,
                                               year=monthGoal.year,
                                               month=monthGoal.month,
                                               distance_minimum=monthGoal.distance_minimum / 1000,
                                               distance_perfect=monthGoal.distance_perfect / 1000)

        return render_template('monthGoalDistanceForm.jinja2', goal=goalModel, goal_id=goal_id)

    @monthGoalsDistance.route('/edit/<int:goal_id>', methods=['POST'])
    @login_required
    @validate()
    def editPost(goal_id: int, form: MonthGoalDistanceFormModel):
        monthGoal = (MonthGoalDistance.query.join(User)
                     .filter(User.username == current_user.username)
                     .filter(MonthGoalDistance.id == goal_id)
                     .first())

        if monthGoal is None:
            abort(404)

        monthGoal.type = TrackType(form.type)
        monthGoal.year = form.year
        monthGoal.month = form.month
        monthGoal.distance_minimum = form.distance_minimum * 1000
        monthGoal.distance_perfect = form.distance_perfect * 1000
        monthGoal.user_id = current_user.id

        LOGGER.debug(f'Updated month goal of type "distance": {monthGoal}')
        db.session.commit()

        return redirect(url_for('monthGoals.listMonthGoals'))

    @monthGoalsDistance.route('/delete/<int:goal_id>')
    @login_required
    def delete(goal_id: int):
        monthGoal = (MonthGoalDistance.query.join(User)
                     .filter(User.username == current_user.username)
                     .filter(MonthGoal.id == goal_id)
                     .first())

        if monthGoal is None:
            abort(404)

        LOGGER.debug(f'Deleted month goal of type "distance": {monthGoal}')
        db.session.delete(monthGoal)
        db.session.commit()

        return redirect(url_for('monthGoals.listMonthGoals'))

    return monthGoalsDistance
