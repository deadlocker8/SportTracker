import logging
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
        rows = (trackClass.query.with_entities(trackClass.startTime, func.sum(trackClass.distance) / 1000)
                .group_by(
            extract('year', trackClass.startTime),
            extract('month', trackClass.startTime),
        ).all())

        monthNames = []
        values = []

        for row in rows:
            monthNames.append(row[0].strftime('%B %y'))
            values.append(float(row[1]))

        return {
            'monthNames': monthNames,
            'values': values,
            'type': trackClass.type
        }

    return charts
