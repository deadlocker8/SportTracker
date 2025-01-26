import logging
from dataclasses import dataclass
from datetime import datetime, date

import flask_babel
from babel.dates import get_month_names
from dateutil.relativedelta import relativedelta
from flask import Blueprint, render_template, redirect, url_for
from flask_babel import format_datetime
from flask_login import login_required, current_user
from pydantic import BaseModel

from sporttracker.logic import Constants
from sporttracker.logic.DateTimeAccess import DateTimeAccess
from sporttracker.logic.QuickFilterState import (
    get_quick_filter_state_from_session,
    QuickFilterState,
)
from sporttracker.logic.model.CustomWorkoutField import CustomWorkoutField
from sporttracker.logic.model.DistanceWorkout import (
    DistanceWorkout,
    get_available_years,
)
from sporttracker.logic.model.GpxMetadata import GpxMetadata
from sporttracker.logic.model.MaintenanceEventInstance import (
    MaintenanceEvent,
    get_maintenance_events_by_year_and_month_by_type,
)
from sporttracker.logic.model.MonthGoal import (
    MonthGoalSummary,
    get_goal_summaries_by_year_and_month_and_types,
)
from sporttracker.logic.model.Participant import get_participants
from sporttracker.logic.model.PlannedTour import get_planned_tours
from sporttracker.logic.model.Workout import (
    get_workout_names_by_type,
    get_workouts_by_year_and_month_by_type,
)
from sporttracker.logic.model.WorkoutType import WorkoutType
from sporttracker.logic.model.User import get_user_by_id
from sporttracker.logic.model.FitnessWorkout import FitnessWorkout

LOGGER = logging.getLogger(Constants.APP_NAME)


@dataclass
class BaseWorkoutModel(DateTimeAccess):
    id: int
    name: str
    type: str
    startTime: datetime
    duration: int
    participants: list[str]
    ownerName: str

    def get_date_time(self) -> datetime:
        return self.startTime


@dataclass
class DistanceWorkoutModel(BaseWorkoutModel):
    distance: int
    averageHeartRate: int | None
    elevationSum: int | None
    gpxMetadata: GpxMetadata | None
    shareCode: str | None

    @staticmethod
    def create_from_workout(
        workout: DistanceWorkout,
    ) -> 'DistanceWorkoutModel':
        return DistanceWorkoutModel(
            id=workout.id,
            name=workout.name,  # type: ignore[arg-type]
            type=workout.type,
            startTime=workout.start_time,  # type: ignore[arg-type]
            distance=workout.distance,
            duration=workout.duration,
            averageHeartRate=workout.average_heart_rate,
            elevationSum=workout.elevation_sum,
            gpxMetadata=workout.get_gpx_metadata(),
            participants=[str(item.id) for item in workout.participants],
            shareCode=workout.share_code,
            ownerName=get_user_by_id(workout.user_id).username,
        )


@dataclass
class FitnessWorkoutModel(BaseWorkoutModel):
    workoutCategories: list[str]
    workoutType: str | None = None

    @staticmethod
    def create_from_workout(
        workout: FitnessWorkout,
    ) -> 'FitnessWorkoutModel':
        return FitnessWorkoutModel(
            id=workout.id,
            name=workout.name,  # type: ignore[arg-type]
            type=workout.type,
            startTime=workout.start_time,  # type: ignore[arg-type]
            duration=workout.duration,
            participants=[str(item.id) for item in workout.participants],
            ownerName=get_user_by_id(workout.user_id).username,
            workoutCategories=workout.get_workout_categories(),
            workoutType=workout.workout_type,
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
    durationHours: int
    durationMinutes: int
    durationSeconds: int
    participants: list[str] | str | None = None

    def calculate_start_time(self) -> datetime:
        return datetime.strptime(f'{self.date} {self.time}', '%Y-%m-%d %H:%M')

    def calculate_duration(self) -> int:
        return 3600 * self.durationHours + 60 * self.durationMinutes + self.durationSeconds


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

        quickFilterState = get_quick_filter_state_from_session()

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
            monthNames=list(
                get_month_names(width='wide', locale=flask_babel.get_locale()).values()
            ),
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

        customFields = (
            CustomWorkoutField.query.filter(CustomWorkoutField.user_id == current_user.id)
            .filter(CustomWorkoutField.workout_type == workoutType)
            .all()
        )

        return render_template(
            f'workouts/workout{workout_type.capitalize()}Form.jinja2',
            customFields=customFields,
            participants=get_participants(),
            trackNames=get_workout_names_by_type(workoutType),
            plannedTours=get_planned_tours([workoutType]),
        )

    return workouts


def __get_month_model(
    monthDate: date,
    quickFilterState: QuickFilterState,
) -> MonthModel:
    workouts = get_workouts_by_year_and_month_by_type(
        monthDate.year,
        monthDate.month,
        quickFilterState.get_active_types(),
    )

    workoutModels: list[DistanceWorkoutModel | FitnessWorkoutModel] = []
    for workout in workouts:
        if workout.type in WorkoutType.get_distance_workout_types():
            workoutModels.append(DistanceWorkoutModel.create_from_workout(workout))
        elif workout.type in WorkoutType.get_workout_workout_types():
            workoutModels.append(FitnessWorkoutModel.create_from_workout(workout))

    maintenanceEvents = get_maintenance_events_by_year_and_month_by_type(
        monthDate.year, monthDate.month, quickFilterState.get_active_types()
    )

    entries = workoutModels + maintenanceEvents
    entries.sort(key=lambda entry: entry.get_date_time(), reverse=True)

    return MonthModel(
        format_datetime(monthDate, format='MMMM yyyy'),
        entries,
        get_goal_summaries_by_year_and_month_and_types(
            monthDate.year,
            monthDate.month,
            quickFilterState.get_active_types(),
        ),
    )
