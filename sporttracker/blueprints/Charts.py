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
from sporttracker.logic.model.CustomSportField import get_custom_fields_by_sport_type
from sporttracker.logic.model.DistanceSport import DistanceSport, get_distance_per_month_by_type
from sporttracker.logic.model.Participant import Participant
from sporttracker.logic.model.Sport import Sport, get_sports_by_year_and_month, get_available_years
from sporttracker.logic.model.SportType import SportType
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
            for sportType in SportType.get_distance_sport_types():
                chartDataDistancePerYear.append(
                    __get_distance_per_year_by_type(sportType, minYear, maxYear)
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
            for sportType in SportType.get_distance_sport_types():
                chartDataDistancePerMonth.append(
                    __get_distance_per_month_by_type(sportType, minYear, maxYear)
                )

        return render_template(
            'charts/chartDistancePerMonth.jinja2',
            chartDataDistancePerMonth=chartDataDistancePerMonth,
        )

    def __get_min_and_max_year() -> tuple[int | None, int | None]:
        result = db.session.query(
            func.min(DistanceSport.start_time),
            func.max(DistanceSport.start_time).filter(DistanceSport.user_id == current_user.id),
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
        customFieldsBySportType = get_custom_fields_by_sport_type()
        # TODO only show chart for distance sports
        for sportType in SportType:
            if not sportType.supports_distance:
                del customFieldsBySportType[sportType]

        return render_template(
            'charts/chartDistancePerCustomFieldChooser.jinja2',
            customFieldsBySportType=customFieldsBySportType,
        )

    @charts.route('/chartDistancePerCustomField/<string:sport_type>/<string:name>')
    @login_required
    def chartDistancePerCustomField(sport_type: str, name: str):
        sportType = SportType(sport_type)  # type: ignore[call-arg]

        customField = DistanceSport.custom_fields[name].astext.cast(String)

        rows = (
            DistanceSport.query.with_entities(func.sum(DistanceSport.distance) / 1000, customField)
            .filter(DistanceSport.user_id == current_user.id)
            .filter(DistanceSport.type == sportType)
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

    @charts.route('/chartDistancePerParticipantChooser/<string:sport_type>')
    @login_required
    def chartDistancePerParticipant(sport_type: str):
        keys = []
        values = []

        participants = Participant.query.filter(Participant.user_id == current_user.id).all()
        for participant in participants:
            keys.append(participant.name)

            distance = (
                DistanceSport.query.with_entities(func.sum(DistanceSport.distance) / 1000)
                .filter(DistanceSport.user_id == current_user.id)
                .filter(DistanceSport.type == sport_type)
                .filter(DistanceSport.participants.any(id=participant.id))
                .scalar()
                or 0
            )
            values.append(float(distance))

        keys.append(gettext('You'))
        distance = (
            DistanceSport.query.with_entities(func.sum(DistanceSport.distance) / 1000)
            .filter(DistanceSport.user_id == current_user.id)
            .filter(DistanceSport.type == sport_type)
            .filter(~DistanceSport.participants.any())
            .scalar()
            or 0
        )
        values.append(float(distance))

        chartDistancePerParticipantData = {'keys': keys, 'values': values}

        return render_template(
            'charts/chartDistancePerParticipant.jinja2',
            chartDistancePerParticipantData=chartDistancePerParticipantData,
            sport_type=sport_type,
        )

    @charts.route('/chartAverageSpeed')
    @login_required
    def chartAverageSpeed():
        minYear, maxYear = __get_min_and_max_year()

        chartDataAverageSpeed: list[dict[str, list | SportType]] = []
        if minYear is None or maxYear is None:
            return chartDataAverageSpeed
        else:
            for sportType in SportType.get_distance_sport_types():
                tracks = (
                    DistanceSport.query.filter(DistanceSport.user_id == current_user.id)
                    .filter(DistanceSport.type == sportType)
                    .order_by(DistanceSport.start_time.asc())
                    .all()
                )

                dates = []
                speedData = []
                for track in tracks:
                    if track.duration is None:
                        continue

                    dates.append(track.start_time.isoformat())
                    speedData.append(round(track.distance / track.duration * 3.6, 2))

                chartDataAverageSpeed.append(
                    {'dates': dates, 'values': speedData, 'type': sportType}
                )

        return render_template(
            'charts/chartAverageSpeed.jinja2', chartDataAverageSpeed=chartDataAverageSpeed
        )

    @charts.route('/durationPerTrackChooser')
    @login_required
    def chartDurationPerTrackChooser():
        return render_template(
            'charts/chartDurationPerTrackChooser.jinja2',
            sportNamesBySportType=__get_sport_names_by_type(False),
        )

    @charts.route('/durationPerTrack/<string:distance_sport_type>/<string:name>')
    @login_required
    def chartDurationPerTrack(distance_sport_type: str, name: str):
        sportType = SportType(distance_sport_type)  # type: ignore[call-arg]

        tracks = (
            DistanceSport.query.filter(DistanceSport.user_id == current_user.id)
            .filter(DistanceSport.type == sportType)
            .filter(DistanceSport.name == name)
            .filter(DistanceSport.duration.is_not(None))
            .order_by(DistanceSport.start_time.asc())
            .all()
        )

        dates = []
        values = []
        texts = []
        for track in tracks:
            if track.duration is None:
                continue

            dates.append(format_datetime(track.start_time, format='short'))
            values.append(track.duration)
            texts.append(f'{format_duration(track.duration)} h')

        chartDataDurationPerTrack = {
            'dates': dates,
            'values': values,
            'texts': texts,
            'type': sportType,
            'min': min(values, default=0) - 300,
            'max': max(values, default=0) + 300,
        }

        return render_template(
            'charts/chartDurationPerTrack.jinja2',
            chartDataDurationPerTrack=chartDataDurationPerTrack,
        )

    @charts.route('/speedPerTrackChooser')
    @login_required
    def chartSpeedPerTrackChooser():
        return render_template(
            'charts/chartSpeedPerTrackChooser.jinja2',
            sportNamesBySportType=__get_sport_names_by_type(True),
        )

    def __get_sport_names_by_type(onlyDistanceBasedSportTypes: bool) -> dict[SportType, list[str]]:
        trackNamesBySportType = {}
        for sportType in SportType:
            if (
                onlyDistanceBasedSportTypes
                and sportType not in SportType.get_distance_sport_types()
            ):
                continue

            rows = (
                DistanceSport.query.with_entities(DistanceSport.name)
                .filter(DistanceSport.user_id == current_user.id)
                .filter(DistanceSport.type == sportType)
                .group_by(DistanceSport.name)
                .having(func.count(DistanceSport.name) >= 2)
                .order_by(asc(func.lower(DistanceSport.name)))
                .all()
            )

            trackNamesBySportType[sportType] = [row[0] for row in rows]
        return trackNamesBySportType

    @charts.route('/speedPerTrack/<string:sport_type>/<string:name>')
    @login_required
    def chartSpeedPerTrack(sport_type: str, name: str):
        sportType = SportType(sport_type)  # type: ignore[call-arg]

        tracks = (
            DistanceSport.query.filter(DistanceSport.user_id == current_user.id)
            .filter(DistanceSport.type == sportType)
            .filter(DistanceSport.name == name)
            .filter(DistanceSport.duration.is_not(None))
            .order_by(DistanceSport.start_time.asc())
            .all()
        )

        dates = []
        values = []
        texts = []
        for track in tracks:
            if track.duration is None:
                continue

            dates.append(format_datetime(track.start_time, format='short'))
            speed = round(track.distance / track.duration * 3.6, 2)
            values.append(speed)
            texts.append(f'{speed} km/h')

        chartDataSpeedPerTrack = {
            'dates': dates,
            'values': values,
            'texts': texts,
            'type': sportType,
            'min': 0,
            'max': max(values, default=0) + 5,
        }

        return render_template(
            'charts/chartSpeedPerTrack.jinja2',
            chartDataSpeedPerTrack=chartDataSpeedPerTrack,
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

            tracks = get_sports_by_year_and_month(year, monthNumber)

            days = []
            for dayNumber in range(1, numberOfDays + 1):
                numberOfTracksPerType = {}
                colors = []
                for sportType in SportType:
                    numberOfTracks = __get_number_of_tracks_per_day_by_type(
                        tracks, sportType, year, monthNumber, dayNumber
                    )
                    numberOfTracksPerType[sportType] = numberOfTracks
                    if numberOfTracks > 0:
                        colors.append(sportType.background_color_hex)

                gradient = __determine_gradient(colors)
                isWeekend = date(year=year, month=monthNumber, day=dayNumber).weekday() in [5, 6]

                days.append(
                    {
                        'number': dayNumber,
                        'numberOfTracksPerType': numberOfTracksPerType,
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

    def __get_number_of_tracks_per_day_by_type(
        sports: list[Sport], sportType: SportType, year: int, month: int, day: int
    ) -> int:
        counter = 0
        for sport in sports:
            if sport.type != sportType:
                continue

            if sport.start_time.year != year:  # type: ignore[attr-defined]
                continue

            if sport.start_time.month != month:  # type: ignore[attr-defined]
                continue

            if sport.start_time.day != day:  # type: ignore[attr-defined]
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
        sportType: SportType, minYear: int, maxYear: int
    ) -> dict[str, Any]:
        monthDistanceSums = get_distance_per_month_by_type(sportType, minYear, maxYear)
        monthNames = []
        values = []
        texts = []

        for monthDistanceSum in monthDistanceSums:
            monthDate = date(year=monthDistanceSum.year, month=monthDistanceSum.month, day=1)
            monthNames.append(format_datetime(monthDate, format='MMMM yyyy'))
            values.append(monthDistanceSum.distanceSum)
            texts.append(f'{monthDistanceSum.distanceSum} km')

        return {'monthNames': monthNames, 'values': values, 'texts': texts, 'type': sportType}

    def __get_distance_per_year_by_type(
        sportType: SportType, minYear: int, maxYear: int
    ) -> dict[str, Any]:
        year = extract('year', DistanceSport.start_time)

        rows = (
            DistanceSport.query.with_entities(
                func.sum(DistanceSport.distance / 1000).label('distanceSum'), year.label('year')
            )
            .filter(DistanceSport.type == sportType)
            .filter(DistanceSport.user_id == current_user.id)
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

        return {'yearNames': yearNames, 'values': values, 'texts': texts, 'type': sportType}

    return charts
