import logging

from flask import Blueprint, render_template, redirect, url_for, abort
from flask_babel import gettext
from flask_login import login_required, current_user
from flask_pydantic import validate
from pydantic import BaseModel

from sporttracker.logic import Constants
from sporttracker.logic.model.MonthGoal import MonthGoalCount, get_month_goal_count_by_id
from sporttracker.logic.model.TrackType import TrackType
from sporttracker.logic.model.db import db

LOGGER = logging.getLogger(Constants.APP_NAME)


class MonthGoalCountFormModel(BaseModel):
    type: str
    year: int
    month: int
    count_minimum: int
    count_perfect: int


class MonthGoalCountMultipleFormModel(BaseModel):
    type: str
    start_year: int
    start_month: int
    end_year: int
    end_month: int
    count_minimum: int
    count_perfect: int


def construct_blueprint():
    monthGoalsCount = Blueprint(
        'monthGoalsCount', __name__, static_folder='static', url_prefix='/goalsCount'
    )

    @monthGoalsCount.route('/add')
    @login_required
    def add():
        return render_template('monthGoals/monthGoalCountForm.jinja2')

    @monthGoalsCount.route('/post', methods=['POST'])
    @login_required
    @validate()
    def addPost(form: MonthGoalCountFormModel):
        monthGoal = MonthGoalCount(
            type=TrackType(form.type),  # type: ignore[call-arg]
            year=form.year,
            month=form.month,
            count_minimum=form.count_minimum,
            count_perfect=form.count_perfect,
            user_id=current_user.id,
        )
        LOGGER.debug(f'Saved new month goal of type "count": {monthGoal}')
        db.session.add(monthGoal)
        db.session.commit()

        return redirect(url_for('monthGoals.listMonthGoals'))

    @monthGoalsCount.route('/addMultiple')
    @login_required
    def addMultiple():
        return render_template('monthGoals/monthGoalCountMultipleForm.jinja2')

    @monthGoalsCount.route('/postMultiple', methods=['POST'])
    @login_required
    @validate()
    def addMultiplePost(form: MonthGoalCountMultipleFormModel):
        currentYear = form.start_year
        currentMonth = form.start_month

        if form.end_year < form.start_year:
            abort(400, gettext('End Year must be greater or equal Start Year.'))

        if form.end_year == form.start_year and form.end_month < form.start_month:
            abort(400, gettext('End Month must be greater or equal Start Month.'))

        monthGoals = []
        while currentYear != form.end_year or currentMonth != form.end_month:
            monthGoals.append(
                MonthGoalCount(
                    type=TrackType(form.type),  # type: ignore[call-arg]
                    year=currentYear,
                    month=currentMonth,
                    count_minimum=form.count_minimum,
                    count_perfect=form.count_perfect,
                    user_id=current_user.id,
                )
            )

            currentMonth += 1
            if currentMonth > 12:
                currentYear += 1
                currentMonth = 1

        LOGGER.debug(
            f'Saved {len(monthGoals)} new month goals of type "count" from {form.start_year}-{form.start_month} to {form.end_year}-{form.end_month}'
        )
        db.session.add_all(monthGoals)
        db.session.commit()

        return redirect(url_for('monthGoals.listMonthGoals'))

    @monthGoalsCount.route('/edit/<int:goal_id>')
    @login_required
    def edit(goal_id: int):
        monthGoal = get_month_goal_count_by_id(goal_id)

        if monthGoal is None:
            abort(404)

        goalModel = MonthGoalCountFormModel(
            type=monthGoal.type.name,
            year=monthGoal.year,
            month=monthGoal.month,
            count_minimum=monthGoal.count_minimum,
            count_perfect=monthGoal.count_perfect,
        )

        return render_template(
            'monthGoals/monthGoalCountForm.jinja2', goal=goalModel, goal_id=goal_id
        )

    @monthGoalsCount.route('/edit/<int:goal_id>', methods=['POST'])
    @login_required
    @validate()
    def editPost(goal_id: int, form: MonthGoalCountFormModel):
        monthGoal = get_month_goal_count_by_id(goal_id)

        if monthGoal is None:
            abort(404)

        monthGoal.type = TrackType(form.type)  # type: ignore[call-arg]
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
        monthGoal = get_month_goal_count_by_id(goal_id)

        if monthGoal is None:
            abort(404)

        LOGGER.debug(f'Deleted month goal of type "count": {monthGoal}')
        db.session.delete(monthGoal)
        db.session.commit()

        return redirect(url_for('monthGoals.listMonthGoals'))

    return monthGoalsCount
