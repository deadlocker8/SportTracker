import logging
from datetime import datetime, date

import flask_babel
from babel.dates import get_month_names
from dateutil.relativedelta import relativedelta
from flask import Blueprint, render_template, redirect, url_for
from flask_babel import format_datetime
from flask_login import login_required, current_user

from sporttracker import Constants
from sporttracker.maintenance.MaintenanceEventInstanceEntity import (
    get_maintenance_events_by_year_and_month_by_type,
)
from sporttracker.monthGoal.MonthGoalService import MonthGoalService
from sporttracker.plannedTour.PlannedTourService import PlannedTourService
from sporttracker.quickFilter.QuickFilterStateEntity import get_quick_filter_state_by_user, QuickFilterState
from sporttracker.user.CustomWorkoutFieldEntity import get_custom_fields_by_workout_type_with_values
from sporttracker.user.ParticipantEntity import get_participants
from sporttracker.workout.WorkoutEntity import (
    get_workout_names_by_type,
    get_workouts_by_year_and_month_by_type,
)
from sporttracker.workout.WorkoutModel import MonthModel, DistanceWorkoutModel, FitnessWorkoutModel
from sporttracker.workout.WorkoutType import WorkoutType
from sporttracker.workout.distance.DistanceWorkoutEntity import (
    get_available_years,
)

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint():
    workouts = Blueprint('workouts', __name__, static_folder='static', url_prefix='/workouts')

    @workouts.route('/', defaults={'year': None, 'month': None})
    @workouts.route('/<int:year>/<int:month>')
    @login_required
    def listWorkouts(year: int, month: int):
        if year is None or month is None:
            now = datetime.now().date()
            return redirect(url_for('workouts.listWorkouts', year=now.year, month=now.month))
        else:
            monthRightSideDate = date(year=year, month=month, day=1)

        quickFilterState = get_quick_filter_state_by_user(current_user.id)

        monthRightSide = __get_month_model(monthRightSideDate, quickFilterState)

        monthLeftSideDate = monthRightSideDate - relativedelta(months=1)
        monthLeftSide = __get_month_model(
            monthLeftSideDate,
            quickFilterState,
        )

        nextMonthDate = monthRightSideDate + relativedelta(months=1)

        return render_template(
            'workout/workouts.jinja2',
            monthLeftSide=monthLeftSide,
            monthRightSide=monthRightSide,
            previousMonthDate=monthLeftSideDate,
            nextMonthDate=nextMonthDate,
            currentMonthDate=datetime.now().date(),
            quickFilterState=quickFilterState,
            year=year,
            month=month,
            availableYears=get_available_years(current_user.id) or [datetime.now().year],
            monthNames=list(get_month_names(width='wide', locale=flask_babel.get_locale()).values()),
        )

    @workouts.route('/add')
    @login_required
    def add():
        return render_template(
            'workout/workoutChooser.jinja2',
        )

    @workouts.route('/add/<string:workout_type>')
    @login_required
    def addType(workout_type: str):
        workoutType = WorkoutType(workout_type)  # type: ignore[call-arg]

        return render_template(
            f'workout/workout{workout_type.capitalize()}Form.jinja2',
            customFields=get_custom_fields_by_workout_type_with_values(workoutType),
            participants=get_participants(),
            workoutNames=get_workout_names_by_type(workoutType),
            plannedTours=PlannedTourService.get_planned_tours([workoutType]),
        )

    return workouts


def __get_month_model(
    monthDate: date,
    quickFilterState: QuickFilterState,
) -> MonthModel:
    workouts = get_workouts_by_year_and_month_by_type(
        monthDate.year,
        monthDate.month,
        quickFilterState.get_active_workout_types(),
    )

    workoutModels: list[DistanceWorkoutModel | FitnessWorkoutModel] = []
    for workout in workouts:
        if workout.type in WorkoutType.get_distance_workout_types():
            workoutModels.append(DistanceWorkoutModel.create_from_workout(workout))
        elif workout.type in WorkoutType.get_fitness_workout_types():
            workoutModels.append(FitnessWorkoutModel.create_from_workout(workout))

    maintenanceEvents = get_maintenance_events_by_year_and_month_by_type(
        monthDate.year, monthDate.month, quickFilterState.get_active_workout_types()
    )

    entries = workoutModels + maintenanceEvents
    entries.sort(key=lambda entry: entry.get_date_time(), reverse=True)

    return MonthModel(
        format_datetime(monthDate, format='MMMM yyyy'),
        entries,
        MonthGoalService.get_goal_summaries_by_year_and_month_and_types(
            monthDate.year,
            monthDate.month,
            quickFilterState.get_active_workout_types(),
            current_user.id,
        ),
    )
