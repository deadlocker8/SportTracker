import logging
from dataclasses import dataclass
from datetime import datetime, date

import flask_babel
from babel.dates import get_month_names
from dateutil.relativedelta import relativedelta
from flask import Blueprint, render_template, redirect, url_for
from flask_babel import format_datetime
from flask_login import login_required, current_user
from pydantic import BaseModel, field_validator

from sporttracker.logic import Constants
from sporttracker.logic.DateTimeAccess import DateTimeAccess
from sporttracker.logic.model.CustomWorkoutField import get_custom_fields_by_workout_type_with_values
from sporttracker.workout.distance.DistanceWorkoutEntity import (
    DistanceWorkout,
    get_available_years,
)
from sporttracker.workout.fitness.FitnessWorkoutEntity import FitnessWorkout
from sporttracker.workout.fitness.FitnessWorkoutCategory import FitnessWorkoutCategoryType
from sporttracker.workout.fitness.FitnessWorkoutType import FitnessWorkoutType
from sporttracker.logic.model.GpxMetadata import GpxMetadata
from sporttracker.maintenance.MaintenanceEventInstanceEntity import (
    MaintenanceEvent,
    get_maintenance_events_by_year_and_month_by_type,
)
from sporttracker.monthGoal.MonthGoalEntity import (
    MonthGoalSummary,
    get_goal_summaries_by_year_and_month_and_types,
)
from sporttracker.logic.model.Participant import get_participants
from sporttracker.logic.model.User import get_user_by_id
from sporttracker.workout.WorkoutEntity import (
    get_workout_names_by_type,
    get_workouts_by_year_and_month_by_type,
)
from sporttracker.workout.WorkoutType import WorkoutType
from sporttracker.logic.model.filterStates.QuickFilterState import get_quick_filter_state_by_user, QuickFilterState
from sporttracker.plannedTour.PlannedTourService import PlannedTourService

LOGGER = logging.getLogger(Constants.APP_NAME)


@dataclass
class BaseWorkoutModel(DateTimeAccess):
    id: int
    name: str
    type: str
    start_time: datetime
    duration: int
    participants: list[str]
    ownerName: str
    average_heart_rate: int | None

    def get_date_time(self) -> datetime:
        return self.start_time


@dataclass
class DistanceWorkoutModel(BaseWorkoutModel):
    distance: int
    elevation_sum: int | None
    gpx_metadata: GpxMetadata | None
    share_code: str | None

    @staticmethod
    def create_from_workout(
        workout: DistanceWorkout,
    ) -> 'DistanceWorkoutModel':
        return DistanceWorkoutModel(
            id=workout.id,
            name=workout.name,  # type: ignore[arg-type]
            type=workout.type,
            start_time=workout.start_time,  # type: ignore[arg-type]
            distance=workout.distance,
            duration=workout.duration,
            average_heart_rate=workout.average_heart_rate,
            elevation_sum=workout.elevation_sum,
            gpx_metadata=workout.get_gpx_metadata(),
            participants=[str(item.id) for item in workout.participants],
            share_code=workout.share_code,
            ownerName=get_user_by_id(workout.user_id).username,
        )


@dataclass
class FitnessWorkoutModel(BaseWorkoutModel):
    fitness_workout_categories: list[FitnessWorkoutCategoryType]
    fitness_workout_type: FitnessWorkoutType | None = None

    @staticmethod
    def create_from_workout(
        workout: FitnessWorkout,
    ) -> 'FitnessWorkoutModel':
        return FitnessWorkoutModel(
            id=workout.id,
            name=workout.name,  # type: ignore[arg-type]
            type=workout.type,
            start_time=workout.start_time,  # type: ignore[arg-type]
            duration=workout.duration,
            average_heart_rate=workout.average_heart_rate,
            participants=[str(item.id) for item in workout.participants],
            ownerName=get_user_by_id(workout.user_id).username,
            fitness_workout_categories=workout.get_workout_categories(),
            fitness_workout_type=workout.fitness_workout_type,
        )


@dataclass
class MonthModel:
    name: str
    entries: list[DistanceWorkoutModel | FitnessWorkoutModel | MaintenanceEvent]
    goals: list[MonthGoalSummary]


class BaseWorkoutFormModel(BaseModel):
    name: str
    type: str
    date: str
    time: str
    duration_hours: int
    duration_minutes: int
    duration_seconds: int
    participants: list[str] | str | None = None
    average_heart_rate: int | None = None

    def calculate_start_time(self) -> datetime:
        return datetime.strptime(f'{self.date} {self.time}', '%Y-%m-%d %H:%M')

    def calculate_duration(self) -> int:
        return 3600 * self.duration_hours + 60 * self.duration_minutes + self.duration_seconds

    @field_validator(*['average_heart_rate'], mode='before')
    def averageHeartRateCheck(cls, value: str, info) -> str | None:
        if isinstance(value, str):
            value = value.strip()
        if value == '':
            return None
        return value


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
            'workouts/workouts.jinja2',
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
            'workouts/workoutChooser.jinja2',
        )

    @workouts.route('/add/<string:workout_type>')
    @login_required
    def addType(workout_type: str):
        workoutType = WorkoutType(workout_type)  # type: ignore[call-arg]

        return render_template(
            f'workouts/workout{workout_type.capitalize()}Form.jinja2',
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
        get_goal_summaries_by_year_and_month_and_types(
            monthDate.year,
            monthDate.month,
            quickFilterState.get_active_workout_types(),
        ),
    )
