from typing import Any

from TheCodeLabs_BaseUtils.DefaultLogger import DefaultLogger
from TheCodeLabs_FlaskUtils.auth.SessionLoginWrapper import require_login
from flask import Blueprint, render_template
from sqlalchemy import extract, func

from logic import Constants
from logic.model.Models import Track, TrackType

LOGGER = DefaultLogger().create_logger_if_not_exists(Constants.APP_NAME)


def construct_blueprint():
    charts = Blueprint('charts', __name__, static_folder='static', url_prefix='/charts')

    @charts.route('/')
    @require_login
    def showCharts():
        chartDataDistancePerMonth = [__get_distance_per_month_by_type(TrackType.BICYCLE),
                                     __get_distance_per_month_by_type(TrackType.RUNNING)]

        return render_template('charts.jinja2', chartDataDistancePerMonth=chartDataDistancePerMonth)

    def __get_distance_per_month_by_type(trackType: TrackType) -> dict[str, Any]:
        rows = (Track.query.with_entities(Track.startTime, func.sum(Track.distance) / 1000)
                .filter(Track.type == trackType)
                .group_by(
            extract('year', Track.startTime),
            extract('month', Track.startTime),
        ).all())

        monthNames = []
        values = []

        for row in rows:
            monthNames.append(row[0].strftime('%B %y'))
            values.append(float(row[1]))

        return {
            'monthNames': monthNames,
            'values': values,
            'type': trackType
        }

    return charts
