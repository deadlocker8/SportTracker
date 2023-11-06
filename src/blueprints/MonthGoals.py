from dataclasses import dataclass
from datetime import date

from TheCodeLabs_BaseUtils.DefaultLogger import DefaultLogger
from flask import Blueprint, render_template, redirect, url_for, abort
from flask_login import login_required, current_user
from flask_pydantic import validate
from pydantic import BaseModel
from sqlalchemy import extract

from logic import Constants
from logic.model.Models import Track, TrackType, db, MonthGoal, User

LOGGER = DefaultLogger().create_logger_if_not_exists(Constants.APP_NAME)


class MonthGoalFormModel(BaseModel):
    type: str
    year: int
    month: int
    distance_minimum: float
    distance_perfect: float


@dataclass
class MonthGoalSummary:
    id: int
    type: TrackType
    name: str
    goal_distance_minimum: float
    goal_distance_perfect: float
    actual_distance: float
    percentage: float
    color: str


def get_month_goal_summary(goal) -> MonthGoalSummary:
    tracks = (Track.query.join(User)
              .filter(User.username == current_user.username)
              .filter(extract('month', Track.startTime) == goal.month)
              .filter(extract('year', Track.startTime) == goal.year)
              .all())

    if tracks:
        actualDistance = sum([t.distance for t in tracks])
    else:
        actualDistance = 0

    color = determine_color(actualDistance, goal)
    name = date(year=goal.year, month=goal.month, day=1).strftime('%B %y')
    percentage = actualDistance / goal.distance_perfect * 100
    return MonthGoalSummary(goal.id,
                            goal.type,
                            name,
                            goal.distance_minimum / 1000,
                            goal.distance_perfect / 1000,
                            actualDistance / 1000,
                            percentage,
                            color)


def determine_color(actualDistance: float, goal: MonthGoal) -> str:
    if actualDistance >= goal.distance_perfect:
        return 'bg-success'
    elif actualDistance >= goal.distance_minimum:
        return 'bg-warning'

    return 'bg-danger'


def construct_blueprint():
    monthGoals = Blueprint('monthGoals', __name__, static_folder='static', url_prefix='/goals')

    @monthGoals.route('/')
    @login_required
    def listMonthGoals():
        goals: list[MonthGoal] = MonthGoal.query.join(User).filter(User.username == current_user.username).order_by(
            MonthGoal.year.desc()).order_by(MonthGoal.month.desc()).all()

        goalSummaries = []
        for goal in goals:
            goalSummaries.append(get_month_goal_summary(goal))

        return render_template('monthGoals.jinja2', monthGoalSummaries=goalSummaries)

    @monthGoals.route('/add')
    @login_required
    def add():
        return render_template('monthGoalForm.jinja2')

    @monthGoals.route('/post', methods=['POST'])
    @login_required
    @validate()
    def addPost(form: MonthGoalFormModel):
        monthGoal = MonthGoal(type=TrackType(form.type),
                              year=form.year,
                              month=form.month,
                              distance_minimum=form.distance_minimum * 1000,
                              distance_perfect=form.distance_perfect * 1000,
                              user_id=current_user.id)
        LOGGER.debug(f'Saved new month goal: {monthGoal}')
        db.session.add(monthGoal)
        db.session.commit()

        return redirect(url_for('monthGoals.listMonthGoals'))

    @monthGoals.route('/edit/<int:goal_id>')
    @login_required
    def edit(goal_id: int):
        monthGoal = (MonthGoal.query.join(User)
                     .filter(User.username == current_user.username)
                     .filter(MonthGoal.id == goal_id)
                     .first())

        if monthGoal is None:
            abort(404)

        goalModel = MonthGoalFormModel(type=monthGoal.type.name,
                                       year=monthGoal.year,
                                       month=monthGoal.month,
                                       distance_minimum=monthGoal.distance_minimum / 1000,
                                       distance_perfect=monthGoal.distance_perfect / 1000)

        return render_template('monthGoalForm.jinja2', goal=goalModel, goal_id=goal_id)

    @monthGoals.route('/edit/<int:goal_id>', methods=['POST'])
    @login_required
    @validate()
    def editPost(goal_id: int, form: MonthGoalFormModel):
        monthGoal = (MonthGoal.query.join(User)
                     .filter(User.username == current_user.username)
                     .filter(MonthGoal.id == goal_id)
                     .first())

        if monthGoal is None:
            abort(404)

        monthGoal.type = TrackType(form.type)
        monthGoal.year = form.year
        monthGoal.month = form.month
        monthGoal.distance_minimum = form.distance_minimum * 1000
        monthGoal.distance_perfect = form.distance_perfect * 1000
        monthGoal.user_id = current_user.id

        LOGGER.debug(f'Updated month goal: {monthGoal}')
        db.session.commit()

        return redirect(url_for('monthGoals.listMonthGoals'))

    @monthGoals.route('/delete/<int:goal_id>')
    @login_required
    def delete(goal_id: int):
        monthGoal = (MonthGoal.query.join(User)
                     .filter(User.username == current_user.username)
                     .filter(MonthGoal.id == goal_id)
                     .first())

        if monthGoal is None:
            abort(404)

        LOGGER.debug(f'Deleted month goal: {monthGoal}')
        db.session.delete(monthGoal)
        db.session.commit()

        return redirect(url_for('monthGoals.listMonthGoals'))

    return monthGoals
