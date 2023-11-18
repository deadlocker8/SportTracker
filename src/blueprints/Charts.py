import logging
from datetime import datetime
from typing import Any

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy import extract, func

from logic import Constants
from logic.model.Models import BikingTrack, RunningTrack, get_distance_per_month_by_type

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
        chartDataDistancePerYear = [__get_distance_per_year_by_type(BikingTrack),
                                    __get_distance_per_year_by_type(RunningTrack)]

        return render_template('chartDistancePerYear.jinja2', chartDataDistancePerYear=chartDataDistancePerYear)

    @charts.route('/distancePerMonth')
    @login_required
    def chartDistancePerMonth():
        chartDataDistancePerMonth = [__get_distance_per_month_by_type(BikingTrack),
                                     __get_distance_per_month_by_type(RunningTrack)]

        return render_template('chartDistancePerMonth.jinja2', chartDataDistancePerMonth=chartDataDistancePerMonth)

    def __get_distance_per_month_by_type(trackClass) -> dict[str, Any]:
        rows = get_distance_per_month_by_type(trackClass)
        monthNames = []
        values = []

        for row in rows:
            month = datetime.strptime(f'{int(row[1])}-{str(int(row[2])).zfill(2)}', '%Y-%m')
            monthNames.append(month.strftime('%B %y'))
            values.append(float(row[0]))

        return {
            'monthNames': monthNames,
            'values': values,
            'type': trackClass.type
        }

    def __get_distance_per_year_by_type(trackClass) -> dict[str, Any]:
        year = extract('year', trackClass.startTime)

        rows = (trackClass.query.with_entities(func.sum(trackClass.distance) / 1000, year)
                .filter(trackClass.user_id == current_user.id)
                .group_by(year)
                .order_by(year)
                .all())

        yearNames = []
        values = []

        for row in rows:
            yearNames.append(row[1])
            values.append(float(row[0]))

        return {
            'yearNames': yearNames,
            'values': values,
            'type': trackClass.type
        }

    return charts
