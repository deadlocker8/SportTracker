import logging
from datetime import date
from typing import Any, Type

from flask import Blueprint, render_template
from flask_babel import gettext
from flask_login import login_required, current_user
from sqlalchemy import extract, func

from logic import Constants
from logic.model.Models import BikingTrack, RunningTrack, get_distance_per_month_by_type, db, Track

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
        maxYear, minYear = __get_min_and_max_year()

        if minYear is None or maxYear is None:
            chartDataDistancePerYear = [[], []]
        else:
            chartDataDistancePerYear = [__get_distance_per_year_by_type(BikingTrack, minYear, maxYear),
                                        __get_distance_per_year_by_type(RunningTrack, minYear, maxYear)]

        return render_template('chartDistancePerYear.jinja2', chartDataDistancePerYear=chartDataDistancePerYear)

    @charts.route('/distancePerMonth')
    @login_required
    def chartDistancePerMonth():
        maxYear, minYear = __get_min_and_max_year()

        if minYear is None or maxYear is None:
            chartDataDistancePerMonth = [[], []]
        else:
            chartDataDistancePerMonth = [__get_distance_per_month_by_type(BikingTrack, minYear, maxYear),
                                         __get_distance_per_month_by_type(RunningTrack, minYear, maxYear)]

        return render_template('chartDistancePerMonth.jinja2', chartDataDistancePerMonth=chartDataDistancePerMonth)

    def __get_min_and_max_year() -> tuple[int | None, int | None]:
        minDateBiking, maxDateBiking = (
            db.session.query(func.min(BikingTrack.startTime), func.max(BikingTrack.startTime)
                             .filter(BikingTrack.user_id == current_user.id))
            .first())
        minDateRunning, maxDateRunning = (
            db.session.query(func.min(RunningTrack.startTime), func.max(RunningTrack.startTime)
                             .filter(RunningTrack.user_id == current_user.id))
            .first())
        minYear = min([y.year for y in [minDateBiking, minDateRunning] if y is not None], default=None)
        maxYear = max([y.year for y in [maxDateBiking, maxDateRunning] if y is not None], default=None)
        return maxYear, minYear

    @charts.route('/chartDistancePerBike')
    @login_required
    def chartDistancePerBike():
        rows = (BikingTrack.query.with_entities(func.sum(BikingTrack.distance) / 1000, BikingTrack.bike)
                .filter(BikingTrack.user_id == current_user.id)
                .group_by(BikingTrack.bike)
                .order_by(BikingTrack.bike)
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

    def __get_distance_per_month_by_type(trackClass: Type[Track], minYear: int, maxYear: int) -> dict[str, Any]:
        monthDistanceSums = get_distance_per_month_by_type(trackClass, minYear, maxYear)
        monthNames = []
        values = []

        for monthDistanceSum in monthDistanceSums:
            monthDate = date(year=monthDistanceSum.year, month=monthDistanceSum.month, day=1)
            monthNames.append(monthDate.strftime('%B %y'))
            values.append(monthDistanceSum.distanceSum)

        return {
            'monthNames': monthNames,
            'values': values,
            'type': trackClass.type
        }

    def __get_distance_per_year_by_type(trackClass: Type[Track], minYear: int, maxYear: int) -> dict[str, Any]:
        year = extract('year', trackClass.startTime)

        rows = (trackClass.query.with_entities(func.sum(trackClass.distance / 1000).label('distanceSum'), year.label('year'))
                .filter(trackClass.user_id == current_user.id)
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
            'type': trackClass.type
        }

    return charts
