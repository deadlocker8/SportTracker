import calendar
import logging
from dataclasses import dataclass
from datetime import date
from typing import Any

import flask_babel
from babel.dates import get_day_names
from flask import Blueprint, render_template, redirect, url_for
from flask_babel import gettext, format_datetime
from flask_login import login_required, current_user
from sqlalchemy import extract, func, String, asc, desc

from sporttracker.helpers.Helpers import format_duration
from sporttracker.logic import Constants
from sporttracker.logic.QuickFilterState import QuickFilterState, get_quick_filter_state_from_session
from sporttracker.logic.model.CustomWorkoutField import (
    get_custom_fields_grouped_by_workout_types,
    get_custom_field_by_id,
)
from sporttracker.logic.model.DistanceWorkout import DistanceWorkout, get_distance_per_month_by_type
from sporttracker.logic.model.Participant import Participant
from sporttracker.logic.model.Workout import (
    Workout,
    get_workouts_by_year_and_month,
    get_available_years,
    get_duration_per_month_by_type,
)
from sporttracker.logic.model.WorkoutType import WorkoutType
from sporttracker.logic.model.db import db
from sporttracker.logic.service.DistanceWorkoutService import DistanceWorkoutService
from sporttracker.logic.tileHunting.MaxSquareCache import MaxSquareCache
from sporttracker.logic.tileHunting.NewVisitedTileCache import NewVisitedTileCache
from sporttracker.logic.tileHunting.VisitedTileService import VisitedTileService

LOGGER = logging.getLogger(Constants.APP_NAME)


@dataclass
class WorkoutName:
    id: int
    name: str


def construct_blueprint(
    newVisitedTileCache: NewVisitedTileCache,
    maxSquareCache: MaxSquareCache,
    distanceWorkoutService: DistanceWorkoutService,
):
    charts = Blueprint('charts', __name__, static_folder='static', url_prefix='/charts')

    @charts.route('/')
    @login_required
    def chartChooser():
        return render_template('charts/chartChooser.jinja2')

    @charts.route('/distancePerYear')
    @login_required
    def chartDistancePerYear():
        minYear, maxYear = __get_min_and_max_year()

        chartDataDistancePerYear: list[dict[str, Any]] = []
        if minYear is not None and maxYear is not None:
            for workoutType in WorkoutType.get_distance_workout_types():
                chartDataDistancePerYear.append(__get_distance_per_year_by_type(workoutType, minYear, maxYear))

        return render_template('charts/chartDistancePerYear.jinja2', chartDataDistancePerYear=chartDataDistancePerYear)

    @charts.route('/distancePerMonth')
    @login_required
    def chartDistancePerMonth():
        minYear, maxYear = __get_min_and_max_year()

        chartDataDistancePerMonth: list[dict[str, Any]] = []
        if minYear is not None and maxYear is not None:
            for workoutType in WorkoutType.get_distance_workout_types():
                chartDataDistancePerMonth.append(__get_distance_per_month_by_type(workoutType, minYear, maxYear))

        return render_template(
            'charts/chartDistancePerMonth.jinja2',
            chartDataDistancePerMonth=chartDataDistancePerMonth,
        )

    def __get_min_and_max_year() -> tuple[int | None, int | None]:
        result = db.session.query(
            func.min(Workout.start_time),
            func.max(Workout.start_time).filter(Workout.user_id == current_user.id),
        ).first()

        if result is None:
            return None, None

        minDate, maxDate = result
        if minDate is None or maxDate is None:
            return None, None

        return minDate.year, maxDate.year

    @charts.route('/chartDistancePerCustomFieldChooser')
    @login_required
    def chartDistancePerCustomFieldChooser():
        customFieldsByWorkoutType = get_custom_fields_grouped_by_workout_types(WorkoutType.get_distance_workout_types())
        return render_template(
            'charts/chartDistancePerCustomFieldChooser.jinja2',
            customFieldsByWorkoutType=customFieldsByWorkoutType,
        )

    @charts.route('/chartDistancePerCustomField/<string:workout_type>/<int:custom_field_id>')
    @login_required
    def chartDistancePerCustomField(workout_type: str, custom_field_id: int):
        workoutType = WorkoutType(workout_type)  # type: ignore[call-arg]

        customField = get_custom_field_by_id(custom_field_id)
        if customField is None:
            return redirect(url_for('charts.chartDistancePerCustomFieldChooser'))

        customFieldOperator = DistanceWorkout.custom_fields[customField.name].astext.cast(String)

        rows = (
            DistanceWorkout.query.with_entities(func.sum(DistanceWorkout.distance) / 1000, customFieldOperator)
            .filter(DistanceWorkout.user_id == current_user.id)
            .filter(DistanceWorkout.type == workoutType)
            .group_by(customFieldOperator)
            .order_by(asc(func.lower(customFieldOperator)))
            .all()
        )

        keys = []
        values = []
        for row in rows:
            values.append(float(row[0]))
            key = row[1]
            if key is None:
                keys.append(gettext('Unknown'))
            else:
                keys.append(key)

        chartDistancePerCustomFieldData = {'keys': keys, 'values': values}

        return render_template(
            'charts/chartDistancePerCustomField.jinja2',
            chartDistancePerCustomFieldData=chartDistancePerCustomFieldData,
            chartTitle=f'{gettext("Distance per custom field")} "{customField.name}"',
        )

    @charts.route('/chartDistancePerParticipantChooser')
    @login_required
    def chartDistancePerParticipantChooser():
        return render_template('charts/chartDistancePerParticipantChooser.jinja2')

    @charts.route('/chartDistancePerParticipantChooser/<string:workout_type>')
    @login_required
    def chartDistancePerParticipant(workout_type: str):
        keys = []
        values = []

        participants = Participant.query.filter(Participant.user_id == current_user.id).all()
        for participant in participants:
            keys.append(participant.name)

            distance = (
                DistanceWorkout.query.with_entities(func.sum(DistanceWorkout.distance) / 1000)
                .filter(DistanceWorkout.user_id == current_user.id)
                .filter(DistanceWorkout.type == workout_type)
                .filter(DistanceWorkout.participants.any(id=participant.id))
                .scalar()
                or 0
            )
            values.append(float(distance))

        keys.append(gettext('You'))
        distance = (
            DistanceWorkout.query.with_entities(func.sum(DistanceWorkout.distance) / 1000)
            .filter(DistanceWorkout.user_id == current_user.id)
            .filter(DistanceWorkout.type == workout_type)
            .filter(~DistanceWorkout.participants.any())
            .scalar()
            or 0
        )
        values.append(float(distance))

        chartDistancePerParticipantData = {'keys': keys, 'values': values}

        return render_template(
            'charts/chartDistancePerParticipant.jinja2',
            chartDistancePerParticipantData=chartDistancePerParticipantData,
            workout_type=workout_type,
            chartTitle=f'{gettext("Distance per participant for workout type ")} "{workout_type}"',
        )

    @charts.route('/chartAverageSpeed')
    @login_required
    def chartAverageSpeed():
        minYear, maxYear = __get_min_and_max_year()

        chartDataAverageSpeed: list[dict[str, list | WorkoutType]] = []
        if minYear is not None and maxYear is not None:
            for workoutType in WorkoutType.get_distance_workout_types():
                workouts = (
                    DistanceWorkout.query.filter(DistanceWorkout.user_id == current_user.id)
                    .filter(DistanceWorkout.type == workoutType)
                    .order_by(DistanceWorkout.start_time.asc())
                    .all()
                )

                dates = []
                speedData = []
                for workout in workouts:
                    if workout.duration is None or workout.duration == 0:
                        continue

                    dates.append(workout.start_time.isoformat())
                    speedData.append(round(workout.distance / workout.duration * 3.6, 2))

                chartDataAverageSpeed.append({'dates': dates, 'values': speedData, 'type': workoutType})

        return render_template('charts/chartAverageSpeed.jinja2', chartDataAverageSpeed=chartDataAverageSpeed)

    @charts.route('/durationPerWorkoutChooser')
    @login_required
    def chartDurationPerWorkoutChooser():
        return render_template(
            'charts/chartDurationPerWorkoutChooser.jinja2',
            workoutNamesByWorkoutType=__get_workout_names_by_type(False),
        )

    @charts.route('/durationPerWorkout/<string:workout_type>/<int:workout_id>')
    @login_required
    def chartDurationPerWorkout(workout_type: str, workout_id: int):
        workoutType = WorkoutType(workout_type)  # type: ignore[call-arg]

        workout = Workout.query.filter(Workout.user_id == current_user.id).filter(Workout.id == workout_id).first()
        if workout is None:
            return redirect(url_for('charts.durationPerWorkoutChooser'))

        workouts = (
            Workout.query.filter(Workout.user_id == current_user.id)
            .filter(Workout.type == workoutType)
            .filter(Workout.name == workout.name)
            .filter(Workout.duration.is_not(None))
            .order_by(Workout.start_time.asc())
            .all()
        )

        dates = []
        values = []
        texts = []
        for workout in workouts:
            if workout.duration is None or workout.duration == 0:
                continue

            dates.append(format_datetime(workout.start_time, format='short'))
            values.append(workout.duration)
            texts.append(f'{format_duration(workout.duration)} h')

        chartDataDurationPerWorkout = {
            'dates': dates,
            'values': values,
            'texts': texts,
            'type': workoutType,
            'min': min(values, default=0) - 300,
            'max': max(values, default=0) + 300,
        }

        return render_template(
            'charts/chartDurationPerWorkout.jinja2',
            chartDataDurationPerWorkout=chartDataDurationPerWorkout,
        )

    @charts.route('/speedPerWorkoutChooser')
    @login_required
    def chartSpeedPerWorkoutChooser():
        return render_template(
            'charts/chartSpeedPerWorkoutChooser.jinja2',
            workoutNamesByWorkoutType=__get_workout_names_by_type(True),
        )

    def __get_workout_names_by_type(
        onlyDistanceBasedWorkoutTypes: bool,
    ) -> dict[WorkoutType, list[WorkoutName]]:
        workoutNamesByWorkoutType = {}
        for workoutType in WorkoutType:
            if onlyDistanceBasedWorkoutTypes and workoutType not in WorkoutType.get_distance_workout_types():
                continue

            rows = (
                Workout.query.with_entities(func.min(Workout.id).label('id'), Workout.name)
                .filter(Workout.user_id == current_user.id)
                .filter(Workout.type == workoutType)
                .group_by(Workout.name)
                .having(func.count(Workout.name) >= 2)
                .order_by(asc(func.lower(Workout.name)))
                .all()
            )

            workoutNamesByWorkoutType[workoutType] = [WorkoutName(row[0], row[1]) for row in rows]
        return workoutNamesByWorkoutType

    @charts.route('/speedPerWorkout/<string:workout_type>/<string:workout_id>')
    @login_required
    def chartSpeedPerWorkout(workout_type: str, workout_id: int):
        workoutType = WorkoutType(workout_type)  # type: ignore[call-arg]

        workout = Workout.query.filter(Workout.user_id == current_user.id).filter(Workout.id == workout_id).first()
        if workout is None:
            return redirect(url_for('charts.durationPerWorkoutChooser'))

        workouts = (
            DistanceWorkout.query.filter(DistanceWorkout.user_id == current_user.id)
            .filter(DistanceWorkout.type == workoutType)
            .filter(DistanceWorkout.name == workout.name)
            .filter(DistanceWorkout.duration.is_not(None))
            .order_by(DistanceWorkout.start_time.asc())
            .all()
        )

        dates = []
        values = []
        texts = []
        for workout in workouts:
            if workout.duration is None or workout.duration == 0:
                continue

            dates.append(format_datetime(workout.start_time, format='short'))
            speed = round(workout.distance / workout.duration * 3.6, 2)
            values.append(speed)
            texts.append(f'{speed} km/h')

        chartDataSpeedPerWorkout = {
            'dates': dates,
            'values': values,
            'texts': texts,
            'type': workoutType,
            'min': 0,
            'max': max(values, default=0) + 5,
        }

        return render_template(
            'charts/chartSpeedPerWorkout.jinja2',
            chartDataSpeedPerWorkout=chartDataSpeedPerWorkout,
            chartTitle=f'{gettext("Speed per Workout")} "{workout.name}"',
        )

    @charts.route('/calendar/<int:year>')
    @login_required
    def chartCalendar(year: int):
        singleWeekDayPattern = __get_single_week_day_pattern()
        calendarData: dict[str, list[dict[str, Any]] | list[str]] = {
            'weekDayPattern': singleWeekDayPattern * 5 + singleWeekDayPattern[:2],
            'months': [],
        }

        quickFilterState = get_quick_filter_state_from_session()

        months = []
        for monthNumber in range(1, 13):
            currentMonthDate = date(year=year, month=monthNumber, day=1)
            __, numberOfDays = calendar.monthrange(year, monthNumber)

            workouts = get_workouts_by_year_and_month(year, monthNumber)

            days = []
            for dayNumber in range(1, numberOfDays + 1):
                numberOfWorkoutsPerType = {}
                colors = []
                for workoutType in quickFilterState.get_active_types():
                    numberOfWorkouts = __get_number_of_workouts_per_day_by_type(
                        workouts, workoutType, year, monthNumber, dayNumber
                    )
                    numberOfWorkoutsPerType[workoutType] = numberOfWorkouts
                    if numberOfWorkouts > 0:
                        colors.append(workoutType.background_color_hex)

                gradient = __determine_gradient(colors)
                isWeekend = date(year=year, month=monthNumber, day=dayNumber).weekday() in [5, 6]

                days.append(
                    {
                        'number': dayNumber,
                        'numberOfWorkoutsPerType': numberOfWorkoutsPerType,
                        'gradient': gradient,
                        'isWeekend': isWeekend,
                    }
                )

            months.append(
                {
                    'number': monthNumber,
                    'name': format_datetime(currentMonthDate, format='MMMM'),
                    'days': days,
                    'startIndex': currentMonthDate.weekday(),
                }
            )

        calendarData['months'] = months

        return render_template(
            'charts/chartCalendar.jinja2',
            calendarData=calendarData,
            availableYears=get_available_years(current_user.id),
            selectedYear=year,
            quickFilterState=quickFilterState,
        )

    def __get_number_of_workouts_per_day_by_type(
        workouts: list[Workout], workoutType: WorkoutType, year: int, month: int, day: int
    ) -> int:
        counter = 0
        for workout in workouts:
            if workout.type != workoutType:
                continue

            if workout.start_time.year != year:  # type: ignore[attr-defined]
                continue

            if workout.start_time.month != month:  # type: ignore[attr-defined]
                continue

            if workout.start_time.day != day:  # type: ignore[attr-defined]
                continue

            counter += 1

        return counter

    def __determine_gradient(colors: list[str]) -> str | None:
        if not colors:
            return None

        colorStops = []
        percentageStep = 100 / len(colors)
        for index, color in enumerate(colors):
            colorStops.append(f'{color} {index * percentageStep}%')
            colorStops.append(f'{color} {(index + 1) * percentageStep}%')

        return f'background-image: repeating-linear-gradient(45deg, {",".join(colorStops)})'

    def __get_single_week_day_pattern() -> list[str]:
        patternWithSundayAsFirstDay = list(get_day_names(width='narrow', locale=flask_babel.get_locale()).values())
        patternWithMondayAsFirstDay = patternWithSundayAsFirstDay[1:] + patternWithSundayAsFirstDay[0:1]
        return patternWithMondayAsFirstDay

    def __get_distance_per_month_by_type(workoutType: WorkoutType, minYear: int, maxYear: int) -> dict[str, Any]:
        monthDistanceSums = get_distance_per_month_by_type(workoutType, minYear, maxYear)
        monthNames = []
        values = []
        texts = []

        for monthDistanceSum in monthDistanceSums:
            monthDate = date(year=monthDistanceSum.year, month=monthDistanceSum.month, day=1)
            monthNames.append(format_datetime(monthDate, format='MMMM yyyy'))
            values.append(monthDistanceSum.distanceSum)
            texts.append(f'{monthDistanceSum.distanceSum} km')

        return {'monthNames': monthNames, 'values': values, 'texts': texts, 'type': workoutType}

    def __get_distance_per_year_by_type(workoutType: WorkoutType, minYear: int, maxYear: int) -> dict[str, Any]:
        year = extract('year', DistanceWorkout.start_time)

        rows = (
            DistanceWorkout.query.with_entities(
                func.sum(DistanceWorkout.distance / 1000).label('distanceSum'), year.label('year')
            )
            .filter(DistanceWorkout.type == workoutType)
            .filter(DistanceWorkout.user_id == current_user.id)
            .group_by(year)
            .order_by(year)
            .all()
        )

        yearNames = []
        values = []
        texts = []
        for currentYear in range(minYear, maxYear + 1):
            for row in rows:
                if row.year == currentYear:
                    yearNames.append(currentYear)
                    values.append(float(row.distanceSum))
                    texts.append(f'{float(row.distanceSum)} km')
                    break
            else:
                yearNames.append(currentYear)
                values.append(0.0)
                texts.append('0.0 km')

        return {'yearNames': yearNames, 'values': values, 'texts': texts, 'type': workoutType}

    @charts.route('/durationPerMonth')
    @login_required
    def chartDurationPerMonth():
        minYear, maxYear = __get_min_and_max_year()

        chartDataDurationPerMonth: list[dict[str, Any]] = []
        if minYear is not None and maxYear is not None:
            for workoutType in WorkoutType:
                chartDataDurationPerMonth.append(__get_duration_per_month_by_type(workoutType, minYear, maxYear))

        return render_template(
            'charts/chartDurationPerMonth.jinja2',
            chartDataDurationPerMonth=chartDataDurationPerMonth,
        )

    def __get_duration_per_month_by_type(workoutType: WorkoutType, minYear: int, maxYear: int) -> dict[str, Any]:
        monthDurationSums = get_duration_per_month_by_type(workoutType, minYear, maxYear)
        monthNames = []
        values = []
        texts = []

        for monthDurationSum in monthDurationSums:
            monthDate = date(year=monthDurationSum.year, month=monthDurationSum.month, day=1)
            monthNames.append(format_datetime(monthDate, format='MMMM yyyy'))
            values.append(monthDurationSum.durationSum)
            texts.append(format_duration(monthDurationSum.durationSum))

        return {'monthNames': monthNames, 'values': values, 'texts': texts, 'type': workoutType}

    @charts.route('/chartMostPerformedWorkoutsChooser')
    @login_required
    def chartMostPerformedWorkoutsChooser():
        return render_template('charts/chartMostPerformedWorkoutsChooser.jinja2')

    @charts.route('/chartMostPerformedWorkoutsChooser/<string:workout_type>')
    @login_required
    def chartMostPerformedWorkouts(workout_type: str):
        rows = (
            Workout.query.with_entities(Workout.name, func.count(Workout.name).label('count'))
            .filter(Workout.user_id == current_user.id)
            .filter(Workout.type == workout_type)
            .group_by(Workout.name)
            .order_by(desc('count'), asc(func.lower(Workout.name)))
            .all()
        )

        chartMostPerformedWorkoutsData = []
        for row in rows:
            chartMostPerformedWorkoutsData.append(
                {'name': row[0], 'count': row.count, 'percentage': row.count / rows[0].count * 100}
            )

        return render_template(
            'charts/chartMostPerformedWorkouts.jinja2',
            chartMostPerformedWorkoutsData=chartMostPerformedWorkoutsData,
            workout_type=WorkoutType(workout_type),  # type: ignore[call-arg]
        )

    @charts.route('/newTilesPerYear')
    @login_required
    def chartNewTilesPerYear():
        minYear, maxYear = __get_min_and_max_year()

        chartDataTotalNumberNewTilesPerYear: list[dict[str, Any]] = []
        chartDataNumberNewTilesPerTypePerYear: list[dict[str, Any]] = []
        if minYear is not None and maxYear is not None:
            visitedTileService = VisitedTileService(
                newVisitedTileCache,
                maxSquareCache,
                QuickFilterState(),
                get_available_years(current_user.id),
                distanceWorkoutService,
            )

            chartDataTotalNumberNewTilesPerYear = __get_total_number_of_new_tiles_per_year_per_type(
                visitedTileService, minYear, maxYear
            )
            chartDataNumberNewTilesPerTypePerYear = __get_number_of_new_tiles_per_year_per_type(
                visitedTileService, minYear, maxYear
            )

        return render_template(
            'charts/chartNewTilesPerYear.jinja2',
            chartDataTotalNumberNewTilesPerYear=chartDataTotalNumberNewTilesPerYear,
            chartDataNumberNewTilesPerTypePerYear=chartDataNumberNewTilesPerTypePerYear,
        )

    def __get_total_number_of_new_tiles_per_year_per_type(
        visitedTileService: VisitedTileService, minYear: int, maxYear: int
    ) -> list[dict[str, Any]]:
        """
        Calculates the total number of new visited tiles per year.
        If a tile is visited for the first time in a year but by multiple workout types it will only be counted once.
        The collected data includes shows the number of new visited tiles for each workout type.
        A tile will be associated with the workout type that first visits the tile.
        """
        newVisitedTilesPerTypePerYear = visitedTileService.get_number_of_new_tiles_per_workout_type_per_year(
            minYear, maxYear, WorkoutType.get_distance_workout_types()
        )

        sumsPerYear = {year: 0 for year in range(minYear, maxYear + 1)}
        for numberOfNewTilesPerYear in newVisitedTilesPerTypePerYear.values():
            for years, tileCount in numberOfNewTilesPerYear.items():
                sumsPerYear[years] = sumsPerYear[years] + tileCount

        result = []
        for workoutType, numberOfNewTilesPerYear in newVisitedTilesPerTypePerYear.items():
            result.append(
                {
                    'yearNames': [
                        f'{year}<br><br>{sumsPerYear[year]} {gettext("Tiles")}'
                        for year, tileCount in numberOfNewTilesPerYear.items()
                    ],
                    'values': list(numberOfNewTilesPerYear.values()),
                    'texts': [str(e) for e in numberOfNewTilesPerYear.values()],
                    'type': workoutType,
                }
            )

        return result

    def __get_number_of_new_tiles_per_year_per_type(
        visitedTileService: VisitedTileService, minYear: int, maxYear: int
    ) -> list[dict[str, Any]]:
        """
        Calculates the number of new visited tiles for each workout type separately.
        This allows tile hunting to be analyzed separately for each workout type.
        So the number of new tiles are calculated for each workout type regardless if they were already visited by another workout type.
        """
        result = []
        for workoutType in WorkoutType.get_distance_workout_types():
            newVisitedTilesPerType = visitedTileService.get_number_of_new_tiles_per_workout_type_per_year(
                minYear, maxYear, [workoutType]
            )

            result.append(
                {
                    'yearNames': list(newVisitedTilesPerType[workoutType].keys()),
                    'values': list(newVisitedTilesPerType[workoutType].values()),
                    'texts': [str(e) for e in newVisitedTilesPerType[workoutType].values()],
                    'type': workoutType,
                }
            )

        return result

    return charts
