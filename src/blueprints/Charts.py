import logging
from datetime import date
from typing import Any, Type

from flask import Blueprint, render_template
from flask_babel import gettext
from flask_login import login_required, current_user
from sqlalchemy import extract, func, String

from logic import Constants
from logic.model.Models import get_distance_per_month_by_type, db, Track, TrackType

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint():
    charts = Blueprint('charts', __name__, static_folder='static', url_prefix='/charts')

    @charts.route('/')
    @login_required
    def chartChooser():
        return render_template('chartChooser.jinja2')

    @charts.route('/distancePerYear')
    @login_required
    def chartDistancePerYear():
        minYear, maxYear = __get_min_and_max_year()

        chartDataDistancePerYear = []
        if minYear is None or maxYear is None:
            return chartDataDistancePerYear
        else:
            for trackType in TrackType:
                chartDataDistancePerYear.append(__get_distance_per_year_by_type(trackType, minYear, maxYear))

        return render_template('chartDistancePerYear.jinja2', chartDataDistancePerYear=chartDataDistancePerYear)

    @charts.route('/distancePerMonth')
    @login_required
    def chartDistancePerMonth():
        minYear, maxYear = __get_min_and_max_year()

        chartDataDistancePerMonth = []
        if minYear is None or maxYear is None:
            return chartDataDistancePerMonth
        else:
            for trackType in TrackType:
                chartDataDistancePerMonth.append(__get_distance_per_month_by_type(trackType, minYear, maxYear))

        return render_template('chartDistancePerMonth.jinja2', chartDataDistancePerMonth=chartDataDistancePerMonth)

    def __get_min_and_max_year() -> tuple[int | None, int | None]:
        minDate, maxDate = (
            db.session.query(func.min(Track.startTime), func.max(Track.startTime)
                             .filter(Track.user_id == current_user.id))
            .first())

        if minDate is None or maxDate is None:
            return None, None

        return minDate.year, maxDate.year

    @charts.route('/chartDistancePerBike')
    @login_required
    def chartDistancePerBike():
        bike = Track.custom_fields['bike'].astext.cast(String)

        rows = (Track.query.with_entities(func.sum(Track.distance) / 1000, bike)
                .filter(Track.user_id == current_user.id)
                .group_by(bike)
                .order_by(bike)
                .all())

        bikeNames = []
        values = []
        for row in rows:
            values.append(float(row[0]))
            name = row[1]
            if name is None:
                bikeNames.append(gettext('Unknown'))
            else:
                bikeNames.append(row[1])

        chartDistancePerBikeData = {'bikeNames': bikeNames, 'values': values}

        return render_template('chartDistancePerBike.jinja2', chartDistancePerBikeData=chartDistancePerBikeData)

    def __get_distance_per_month_by_type(trackType: TrackType, minYear: int, maxYear: int) -> dict[str, Any]:
        monthDistanceSums = get_distance_per_month_by_type(trackType, minYear, maxYear)
        monthNames = []
        values = []

        for monthDistanceSum in monthDistanceSums:
            monthDate = date(year=monthDistanceSum.year, month=monthDistanceSum.month, day=1)
            monthNames.append(monthDate.strftime('%B %y'))
            values.append(monthDistanceSum.distanceSum)

        return {
            'monthNames': monthNames,
            'values': values,
            'type': trackType
        }

    def __get_distance_per_year_by_type(trackType: TrackType, minYear: int, maxYear: int) -> dict[str, Any]:
        year = extract('year', Track.startTime)

        rows = (Track.query.with_entities(func.sum(Track.distance / 1000).label('distanceSum'), year.label('year'))
                .filter(Track.type == trackType)
                .filter(Track.user_id == current_user.id)
                .group_by(year)
                .order_by(year)
                .all())

        yearNames = []
        values = []
        for year in range(minYear, maxYear + 1):
            for row in rows:
                if row.year == year:
                    yearNames.append(year)
                    values.append(float(row.distanceSum))
                    break
            else:
                yearNames.append(year)
                values.append(0.0)

        return {
            'yearNames': yearNames,
            'values': values,
            'type': trackType
        }

    return charts
