import logging

from flask import Blueprint, render_template, redirect, url_for, abort
from flask_babel import gettext
from flask_login import login_required, current_user
from flask_pydantic import validate
from pydantic import BaseModel

from sporttracker.logic import Constants
from sporttracker.logic.model.MonthGoal import MonthGoalDuration, get_month_goal_duration_by_id
from sporttracker.logic.model.WorkoutType import WorkoutType
from sporttracker.logic.model.db import db

LOGGER = logging.getLogger(Constants.APP_NAME)


class MonthGoalDurationFormModel(BaseModel):
    type: str
    year: int
    month: int
    duration_minimum_hours: int
    duration_minimum_minutes: int
    duration_perfect_hours: int
    duration_perfect_minutes: int

    def calculate_duration_minimum(self) -> int:
        return self.__calculate_duration(self.duration_minimum_hours, self.duration_minimum_minutes)

    def calculate_duration_perfect(self) -> int:
        return self.__calculate_duration(self.duration_perfect_hours, self.duration_perfect_minutes)

    @staticmethod
    def __calculate_duration(hours: int, minutes: int) -> int:
        return 3600 * hours + 60 * minutes


class MonthGoalDurationMultipleFormModel(BaseModel):
    type: str
    start_year: int
    start_month: int
    end_year: int
    end_month: int
    duration_minimum_hours: int
    duration_minimum_minutes: int
    duration_perfect_hours: int
    duration_perfect_minutes: int

    def calculate_duration_minimum(self) -> int:
        return self.__calculate_duration(self.duration_minimum_hours, self.duration_minimum_minutes)

    def calculate_duration_perfect(self) -> int:
        return self.__calculate_duration(self.duration_perfect_hours, self.duration_perfect_minutes)

    @staticmethod
    def __calculate_duration(hours: int, minutes: int) -> int:
        return 3600 * hours + 60 * minutes


def construct_blueprint():
    monthGoalsDuration = Blueprint(
        'monthGoalsDuration', __name__, static_folder='static', url_prefix='/goalsDuration'
    )

    @monthGoalsDuration.route('/add')
    @login_required
    def add():
        return render_template('monthGoals/monthGoalDurationForm.jinja2')

    @monthGoalsDuration.route('/post', methods=['POST'])
    @login_required
    @validate()
    def addPost(form: MonthGoalDurationFormModel):
        monthGoal = MonthGoalDuration(
            type=WorkoutType(form.type),  # type: ignore[call-arg]
            year=form.year,
            month=form.month,
            duration_minimum=form.calculate_duration_minimum(),
            duration_perfect=form.calculate_duration_perfect(),
            user_id=current_user.id,
        )
        LOGGER.debug(f'Saved new month goal of type "duration": {monthGoal}')
        db.session.add(monthGoal)
        db.session.commit()

        return redirect(url_for('monthGoals.listMonthGoals'))

    @monthGoalsDuration.route('/addMultiple')
    @login_required
    def addMultiple():
        return render_template('monthGoals/monthGoalDurationMultipleForm.jinja2')

    @monthGoalsDuration.route('/postMultiple', methods=['POST'])
    @login_required
    @validate()
    def addMultiplePost(form: MonthGoalDurationMultipleFormModel):
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
                MonthGoalDuration(
                    type=WorkoutType(form.type),  # type: ignore[call-arg]
                    year=currentYear,
                    month=currentMonth,
                    duration_minimum=form.calculate_duration_minimum(),
                    duration_perfect=form.calculate_duration_perfect(),
                    user_id=current_user.id,
                )
            )

            currentMonth += 1
            if currentMonth > 12:
                currentYear += 1
                currentMonth = 1

        LOGGER.debug(
            f'Saved {len(monthGoals)} new month goals of type "duration" from {form.start_year}-{form.start_month} to {form.end_year}-{form.end_month}'
        )
        db.session.add_all(monthGoals)
        db.session.commit()

        return redirect(url_for('monthGoals.listMonthGoals'))

    @monthGoalsDuration.route('/edit/<int:goal_id>')
    @login_required
    def edit(goal_id: int):
        monthGoal = get_month_goal_duration_by_id(goal_id)

        if monthGoal is None:
            abort(404)

        goalModel = MonthGoalDurationFormModel(
            type=monthGoal.type.name,
            year=monthGoal.year,
            month=monthGoal.month,
            duration_minimum_hours=monthGoal.duration_minimum // 3600,
            duration_minimum_minutes=monthGoal.duration_minimum % 3600 // 60,
            duration_perfect_hours=monthGoal.duration_perfect // 3600,
            duration_perfect_minutes=monthGoal.duration_perfect % 3600 // 60,
        )

        return render_template(
            'monthGoals/monthGoalDurationForm.jinja2', goal=goalModel, goal_id=goal_id
        )

    @monthGoalsDuration.route('/edit/<int:goal_id>', methods=['POST'])
    @login_required
    @validate()
    def editPost(goal_id: int, form: MonthGoalDurationFormModel):
        monthGoal = get_month_goal_duration_by_id(goal_id)

        if monthGoal is None:
            abort(404)

        monthGoal.type = WorkoutType(form.type)  # type: ignore[call-arg]
        monthGoal.year = form.year
        monthGoal.month = form.month
        monthGoal.duration_minimum = form.calculate_duration_minimum()  # type: ignore[assignment]
        monthGoal.duration_perfect = form.calculate_duration_perfect()  # type: ignore[assignment]
        monthGoal.user_id = current_user.id

        LOGGER.debug(f'Updated month goal of type "duration": {monthGoal}')
        db.session.commit()

        return redirect(url_for('monthGoals.listMonthGoals'))

    @monthGoalsDuration.route('/delete/<int:goal_id>')
    @login_required
    def delete(goal_id: int):
        monthGoal = get_month_goal_duration_by_id(goal_id)

        if monthGoal is None:
            abort(404)

        LOGGER.debug(f'Deleted month goal of type "duration": {monthGoal}')
        db.session.delete(monthGoal)
        db.session.commit()

        return redirect(url_for('monthGoals.listMonthGoals'))

    return monthGoalsDuration
