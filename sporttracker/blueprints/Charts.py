import calendar
import logging
from datetime import date
from typing import Any

import flask_babel
from babel.dates import get_day_names
from flask import Blueprint, render_template
from flask_babel import gettext, format_datetime
from flask_login import login_required, current_user
from sqlalchemy import extract, func, String, asc

from sporttracker.helpers.Helpers import format_duration
from sporttracker.logic import Constants
from sporttracker.logic.model.CustomWorkoutField import get_custom_fields_by_workout_type
from sporttracker.logic.model.DistanceWorkout import DistanceWorkout, get_distance_per_month_by_type
from sporttracker.logic.model.Participant import Participant
from sporttracker.logic.model.Workout import (
    Workout,
    get_workouts_by_year_and_month,
    get_available_years,
)
from sporttracker.logic.model.WorkoutType import WorkoutType
from sporttracker.logic.model.db import db

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint():
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
        if minYear is None or maxYear is None:
            return chartDataDistancePerYear
        else:
            for workoutType in WorkoutType.get_distance_workout_types():
                chartDataDistancePerYear.append(
                    __get_distance_per_year_by_type(workoutType, minYear, maxYear)
                )

        return render_template(
            'charts/chartDistancePerYear.jinja2', chartDataDistancePerYear=chartDataDistancePerYear
        )

    @charts.route('/distancePerMonth')
    @login_required
    def chartDistancePerMonth():
        minYear, maxYear = __get_min_and_max_year()

        chartDataDistancePerMonth: list[dict[str, Any]] = []
        if minYear is None or maxYear is None:
            return chartDataDistancePerMonth
        else:
            for workoutType in WorkoutType.get_distance_workout_types():
                chartDataDistancePerMonth.append(
                    __get_distance_per_month_by_type(workoutType, minYear, maxYear)
                )

        return render_template(
            'charts/chartDistancePerMonth.jinja2',
            chartDataDistancePerMonth=chartDataDistancePerMonth,
        )

    def __get_min_and_max_year() -> tuple[int | None, int | None]:
        result = db.session.query(
            func.min(DistanceWorkout.start_time),
            func.max(DistanceWorkout.start_time).filter(DistanceWorkout.user_id == current_user.id),
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
        customFieldsByWorkoutType = get_custom_fields_by_workout_type(
            WorkoutType.get_distance_workout_types()
        )
        return render_template(
            'charts/chartDistancePerCustomFieldChooser.jinja2',
            customFieldsByWorkoutType=customFieldsByWorkoutType,
        )

    @charts.route('/chartDistancePerCustomField/<string:workout_type>/<string:name>')
    @login_required
    def chartDistancePerCustomField(workout_type: str, name: str):
        workoutType = WorkoutType(workout_type)  # type: ignore[call-arg]

        customField = DistanceWorkout.custom_fields[name].astext.cast(String)

        rows = (
            DistanceWorkout.query.with_entities(
                func.sum(DistanceWorkout.distance) / 1000, customField
            )
            .filter(DistanceWorkout.user_id == current_user.id)
            .filter(DistanceWorkout.type == workoutType)
            .group_by(customField)
            .order_by(asc(func.lower(customField)))
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
            customFieldName=name,
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
        )

    @charts.route('/chartAverageSpeed')
    @login_required
    def chartAverageSpeed():
        minYear, maxYear = __get_min_and_max_year()

        chartDataAverageSpeed: list[dict[str, list | WorkoutType]] = []
        if minYear is None or maxYear is None:
            return chartDataAverageSpeed
        else:
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

                chartDataAverageSpeed.append(
                    {'dates': dates, 'values': speedData, 'type': workoutType}
                )

        return render_template(
            'charts/chartAverageSpeed.jinja2', chartDataAverageSpeed=chartDataAverageSpeed
        )

    @charts.route('/durationPerWorkoutChooser')
    @login_required
    def chartDurationPerWorkoutChooser():
        return render_template(
            'charts/chartDurationPerWorkoutChooser.jinja2',
            workoutNamesByWorkoutType=__get_workout_names_by_type(False),
        )

    @charts.route('/durationPerWorkout/<string:workout_type>/<string:name>')
    @login_required
    def chartDurationPerWorkout(workout_type: str, name: str):
        workoutType = WorkoutType(workout_type)  # type: ignore[call-arg]

        workouts = (
            DistanceWorkout.query.filter(DistanceWorkout.user_id == current_user.id)
            .filter(DistanceWorkout.type == workoutType)
            .filter(DistanceWorkout.name == name)
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
    ) -> dict[WorkoutType, list[str]]:
        workoutNamesByWorkoutType = {}
        for workoutType in WorkoutType:
            if (
                onlyDistanceBasedWorkoutTypes
                and workoutType not in WorkoutType.get_distance_workout_types()
            ):
                continue

            rows = (
                DistanceWorkout.query.with_entities(DistanceWorkout.name)
                .filter(DistanceWorkout.user_id == current_user.id)
                .filter(DistanceWorkout.type == workoutType)
                .group_by(DistanceWorkout.name)
                .having(func.count(DistanceWorkout.name) >= 2)
                .order_by(asc(func.lower(DistanceWorkout.name)))
                .all()
            )

            workoutNamesByWorkoutType[workoutType] = [row[0] for row in rows]
        return workoutNamesByWorkoutType

    @charts.route('/speedPerWorkout/<string:workout_type>/<string:name>')
    @login_required
    def chartSpeedPerWorkout(workout_type: str, name: str):
        workoutType = WorkoutType(workout_type)  # type: ignore[call-arg]

        workouts = (
            DistanceWorkout.query.filter(DistanceWorkout.user_id == current_user.id)
            .filter(DistanceWorkout.type == workoutType)
            .filter(DistanceWorkout.name == name)
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
        )

    @charts.route('/calendar/<int:year>')
    @login_required
    def chartCalendar(year: int):
        singleWeekDayPattern = __get_single_week_day_pattern()
        calendarData: dict[str, list[dict[str, Any]] | list[str]] = {
            'weekDayPattern': singleWeekDayPattern * 5 + singleWeekDayPattern[:2],
            'months': [],
        }

        months = []
        for monthNumber in range(1, 13):
            currentMonthDate = date(year=year, month=monthNumber, day=1)
            __, numberOfDays = calendar.monthrange(year, monthNumber)

            workouts = get_workouts_by_year_and_month(year, monthNumber)

            days = []
            for dayNumber in range(1, numberOfDays + 1):
                numberOfWorkoutsPerType = {}
                colors = []
                for workoutType in WorkoutType:
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
        patternWithSundayAsFirstDay = list(
            get_day_names(width='narrow', locale=flask_babel.get_locale()).values()
        )
        patternWithMondayAsFirstDay = (
            patternWithSundayAsFirstDay[1:] + patternWithSundayAsFirstDay[0:1]
        )
        return patternWithMondayAsFirstDay

    def __get_distance_per_month_by_type(
        workoutType: WorkoutType, minYear: int, maxYear: int
    ) -> dict[str, Any]:
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

    def __get_distance_per_year_by_type(
        workoutType: WorkoutType, minYear: int, maxYear: int
    ) -> dict[str, Any]:
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

    return charts
