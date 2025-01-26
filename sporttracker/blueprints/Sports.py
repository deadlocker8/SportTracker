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
from sporttracker.logic.model.CustomSportField import CustomSportField
from sporttracker.logic.model.DistanceSport import (
    DistanceSport,
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
from sporttracker.logic.model.Sport import (
    get_sport_names_by_type,
    get_sports_by_year_and_month_by_type,
)
from sporttracker.logic.model.WorkoutType import WorkoutType
from sporttracker.logic.model.User import get_user_by_id
from sporttracker.logic.model.WorkoutSport import WorkoutSport

LOGGER = logging.getLogger(Constants.APP_NAME)


@dataclass
class BaseSportModel(DateTimeAccess):
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
class DistanceSportModel(BaseSportModel):
    distance: int
    averageHeartRate: int | None
    elevationSum: int | None
    gpxMetadata: GpxMetadata | None
    shareCode: str | None

    @staticmethod
    def create_from_sport(
        sport: DistanceSport,
    ) -> 'DistanceSportModel':
        return DistanceSportModel(
            id=sport.id,
            name=sport.name,  # type: ignore[arg-type]
            type=sport.type,
            startTime=sport.start_time,  # type: ignore[arg-type]
            distance=sport.distance,
            duration=sport.duration,
            averageHeartRate=sport.average_heart_rate,
            elevationSum=sport.elevation_sum,
            gpxMetadata=sport.get_gpx_metadata(),
            participants=[str(item.id) for item in sport.participants],
            shareCode=sport.share_code,
            ownerName=get_user_by_id(sport.user_id).username,
        )


@dataclass
class WorkoutSportModel(BaseSportModel):
    workoutCategories: list[str]
    workoutType: str | None = None

    @staticmethod
    def create_from_sport(
        sport: WorkoutSport,
    ) -> 'WorkoutSportModel':
        return WorkoutSportModel(
            id=sport.id,
            name=sport.name,  # type: ignore[arg-type]
            type=sport.type,
            startTime=sport.start_time,  # type: ignore[arg-type]
            duration=sport.duration,
            participants=[str(item.id) for item in sport.participants],
            ownerName=get_user_by_id(sport.user_id).username,
            workoutCategories=sport.get_workout_categories(),
            workoutType=sport.workout_type,
        )


@dataclass
class MonthModel:
    name: str
    entries: list[DistanceSportModel | WorkoutSportModel | MaintenanceEvent]
    goals: list[MonthGoalSummary]


class BaseSportFormModel(BaseModel):
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
    sports = Blueprint('sports', __name__, static_folder='static', url_prefix='/sports')

    @sports.route('/', defaults={'year': None, 'month': None})
    @sports.route('/<int:year>/<int:month>')
    @login_required
    def listSports(year: int, month: int):
        if year is None or month is None:
            now = datetime.now().date()
            return redirect(url_for('sports.listSports', year=now.year, month=now.month))
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
            'sports/sports.jinja2',
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

    @sports.route('/add')
    @login_required
    def add():
        return render_template(
            'sports/sportChooser.jinja2',
        )

    @sports.route('/add/<string:sport_type>')
    @login_required
    def addType(sport_type: str):
        workoutType = WorkoutType(sport_type)  # type: ignore[call-arg]

        customFields = (
            CustomSportField.query.filter(CustomSportField.user_id == current_user.id)
            .filter(CustomSportField.sport_type == workoutType)
            .all()
        )

        return render_template(
            f'sports/sport{sport_type.capitalize()}Form.jinja2',
            customFields=customFields,
            participants=get_participants(),
            trackNames=get_sport_names_by_type(workoutType),
            plannedTours=get_planned_tours([workoutType]),
        )

    return sports


def __get_month_model(
    monthDate: date,
    quickFilterState: QuickFilterState,
) -> MonthModel:
    sports = get_sports_by_year_and_month_by_type(
        monthDate.year,
        monthDate.month,
        quickFilterState.get_active_types(),
    )

    sportModels: list[DistanceSportModel | WorkoutSportModel] = []
    for sport in sports:
        if sport.type in WorkoutType.get_distance_sport_types():
            sportModels.append(DistanceSportModel.create_from_sport(sport))
        elif sport.type in WorkoutType.get_workout_sport_types():
            sportModels.append(WorkoutSportModel.create_from_sport(sport))

    maintenanceEvents = get_maintenance_events_by_year_and_month_by_type(
        monthDate.year, monthDate.month, quickFilterState.get_active_types()
    )

    entries = sportModels + maintenanceEvents
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
