from dataclasses import dataclass
from datetime import date

from TheCodeLabs_BaseUtils.DefaultLogger import DefaultLogger
from TheCodeLabs_FlaskUtils.auth.SessionLoginWrapper import require_login
from flask import Blueprint, render_template, session, redirect, url_for
from flask_pydantic import validate
from pydantic import BaseModel
from sqlalchemy import extract

from logic import Constants
from logic.model.Models import Track, TrackType, db, MonthGoal, User

LOGGER = DefaultLogger().create_logger_if_not_exists(Constants.APP_NAME)


class MonthGoalFormModel(BaseModel):
    year: int
    month: int
    distance_minimum: float
    distance_perfect: float


@dataclass
class MonthGoalSummary:
    name: str
    goal_distance_minimum: float
    goal_distance_perfect: float
    actual_distance: float
    percentage: float
    color: str


def get_month_goal_summary(goal) -> MonthGoalSummary:
    tracks = (Track.query.join(User)
              .filter(User.username == session['username'])
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
    return MonthGoalSummary(name,
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
    @require_login
    def listMonthGoals():
        goals: list[MonthGoal] = MonthGoal.query.join(User).filter(User.username == session['username']).order_by(
            MonthGoal.year.desc()).order_by(MonthGoal.month.desc()).all()

        goalSummaries = []
        for goal in goals:
            goalSummaries.append(get_month_goal_summary(goal))

        return render_template('monthGoals.jinja2', monthGoalSummaries=goalSummaries)

    @monthGoals.route('/add')
    @require_login
    def add():
        return render_template('monthGoalAdd.jinja2')

    @monthGoals.route('/post', methods=['POST'])
    @require_login
    @validate()
    def addPost(form: MonthGoalFormModel):
        monthGoal = MonthGoal(type=TrackType.BICYCLE,
                              year=form.year,
                              month=form.month,
                              distance_minimum=form.distance_minimum * 1000,
                              distance_perfect=form.distance_perfect * 1000,
                              user_id=session['userId'])
        LOGGER.debug(f'Saved new month goal: {monthGoal}')
        db.session.add(monthGoal)
        db.session.commit()

        return redirect(url_for('monthGoals.listMonthGoals'))

    return monthGoals
