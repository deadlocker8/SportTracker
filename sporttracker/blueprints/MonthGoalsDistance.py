import logging

from flask import Blueprint, render_template, redirect, url_for, abort
from flask_babel import gettext
from flask_login import login_required, current_user
from flask_pydantic import validate
from pydantic import BaseModel

from sporttracker.logic import Constants
from sporttracker.logic.model.MonthGoal import MonthGoalDistance, get_month_goal_distance_by_id
from sporttracker.logic.model.TrackType import TrackType
from sporttracker.logic.model.db import db

LOGGER = logging.getLogger(Constants.APP_NAME)


class MonthGoalDistanceFormModel(BaseModel):
    type: str
    year: int
    month: int
    distance_minimum: float
    distance_perfect: float


class MonthGoalDistanceMultipleFormModel(BaseModel):
    type: str
    start_year: int
    start_month: int
    end_year: int
    end_month: int
    distance_minimum: float
    distance_perfect: float


def construct_blueprint():
    monthGoalsDistance = Blueprint(
        'monthGoalsDistance', __name__, static_folder='static', url_prefix='/goalsDistance'
    )

    @monthGoalsDistance.route('/add')
    @login_required
    def add():
        return render_template('monthGoals/monthGoalDistanceForm.jinja2')

    @monthGoalsDistance.route('/post', methods=['POST'])
    @login_required
    @validate()
    def addPost(form: MonthGoalDistanceFormModel):
        monthGoal = MonthGoalDistance(
            type=TrackType(form.type),  # type: ignore[call-arg]
            year=form.year,
            month=form.month,
            distance_minimum=form.distance_minimum * 1000,
            distance_perfect=form.distance_perfect * 1000,
            user_id=current_user.id,
        )
        LOGGER.debug(f'Saved new month goal of type "distance": {monthGoal}')
        db.session.add(monthGoal)
        db.session.commit()

        return redirect(url_for('monthGoals.listMonthGoals'))

    @monthGoalsDistance.route('/addMultiple')
    @login_required
    def addMultiple():
        return render_template('monthGoals/monthGoalDistanceMultipleForm.jinja2')

    @monthGoalsDistance.route('/postMultiple', methods=['POST'])
    @login_required
    @validate()
    def addMultiplePost(form: MonthGoalDistanceMultipleFormModel):
        currentYear = form.start_year
        currentMonth = form.start_month

        if form.end_year < form.start_year:
            abort(400, gettext('End Year must be greater or equal Start Year.'))

        if form.end_year == form.start_year and form.end_month < form.start_month:
            abort(400, gettext('End Month must be greater or equal Start Month.'))

        monthGoals = []
        while currentYear < form.end_year or (
            currentYear == form.end_year and currentMonth <= form.end_month
        ):
            monthGoals.append(
                MonthGoalDistance(
                    type=TrackType(form.type),  # type: ignore[call-arg]
                    year=currentYear,
                    month=currentMonth,
                    distance_minimum=form.distance_minimum * 1000,
                    distance_perfect=form.distance_perfect * 1000,
                    user_id=current_user.id,
                )
            )

            currentMonth += 1
            if currentMonth > 12:
                currentYear += 1
                currentMonth = 1

        LOGGER.debug(
            f'Saved {len(monthGoals)} new month goals of type "distance" from {form.start_year}-{form.start_month} to {form.end_year}-{form.end_month}'
        )
        db.session.add_all(monthGoals)
        db.session.commit()

        return redirect(url_for('monthGoals.listMonthGoals'))

    @monthGoalsDistance.route('/edit/<int:goal_id>')
    @login_required
    def edit(goal_id: int):
        monthGoal = get_month_goal_distance_by_id(goal_id)

        if monthGoal is None:
            abort(404)

        goalModel = MonthGoalDistanceFormModel(
            type=monthGoal.type.name,
            year=monthGoal.year,
            month=monthGoal.month,
            distance_minimum=monthGoal.distance_minimum / 1000,
            distance_perfect=monthGoal.distance_perfect / 1000,
        )

        return render_template(
            'monthGoals/monthGoalDistanceForm.jinja2', goal=goalModel, goal_id=goal_id
        )

    @monthGoalsDistance.route('/edit/<int:goal_id>', methods=['POST'])
    @login_required
    @validate()
    def editPost(goal_id: int, form: MonthGoalDistanceFormModel):
        monthGoal = get_month_goal_distance_by_id(goal_id)

        if monthGoal is None:
            abort(404)

        monthGoal.type = TrackType(form.type)  # type: ignore[call-arg]
        monthGoal.year = form.year
        monthGoal.month = form.month
        monthGoal.distance_minimum = form.distance_minimum * 1000  # type: ignore[assignment]
        monthGoal.distance_perfect = form.distance_perfect * 1000  # type: ignore[assignment]
        monthGoal.user_id = current_user.id

        LOGGER.debug(f'Updated month goal of type "distance": {monthGoal}')
        db.session.commit()

        return redirect(url_for('monthGoals.listMonthGoals'))

    @monthGoalsDistance.route('/delete/<int:goal_id>')
    @login_required
    def delete(goal_id: int):
        monthGoal = get_month_goal_distance_by_id(goal_id)

        if monthGoal is None:
            abort(404)

        LOGGER.debug(f'Deleted month goal of type "distance": {monthGoal}')
        db.session.delete(monthGoal)
        db.session.commit()

        return redirect(url_for('monthGoals.listMonthGoals'))

    return monthGoalsDistance
