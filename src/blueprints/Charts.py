import logging
from datetime import datetime
from typing import Any

from flask import Blueprint, render_template
from flask_login import login_required
from sqlalchemy import extract, func

from logic import Constants
from logic.model.Models import BikingTrack, RunningTrack

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint():
    charts = Blueprint('charts', __name__, static_folder='static', url_prefix='/charts')

    @charts.route('/')
    @login_required
    def showCharts():
        chartDataDistancePerMonth = [__get_distance_per_month_by_type(BikingTrack),
                                     __get_distance_per_month_by_type(RunningTrack)]

        return render_template('charts.jinja2', chartDataDistancePerMonth=chartDataDistancePerMonth)

    def __get_distance_per_month_by_type(trackClass) -> dict[str, Any]:
        year = extract('year', trackClass.startTime)
        month = extract('month', trackClass.startTime)

        rows = (trackClass.query.with_entities(func.sum(trackClass.distance) / 1000, year, month)
                .group_by(year, month)
                .order_by(year, month)
                .all())

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

    return charts
