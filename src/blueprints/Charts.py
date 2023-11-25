import logging
from datetime import date
from typing import Any

from flask import Blueprint, render_template
from flask_babel import gettext
from flask_login import login_required, current_user
from sqlalchemy import extract, func, String

from logic import Constants
from logic.model.Models import get_distance_per_month_by_type, db, Track, TrackType, CustomTrackField, \
    get_custom_fields_by_track_type

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

        chartDataDistancePerYear = []
        if minYear is None or maxYear is None:
            return chartDataDistancePerYear
        else:
            for trackType in TrackType:
                chartDataDistancePerYear.append(__get_distance_per_year_by_type(trackType, minYear, maxYear))

        return render_template('charts/chartDistancePerYear.jinja2', chartDataDistancePerYear=chartDataDistancePerYear)

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

        return render_template('charts/chartDistancePerMonth.jinja2', chartDataDistancePerMonth=chartDataDistancePerMonth)

    def __get_min_and_max_year() -> tuple[int | None, int | None]:
        minDate, maxDate = (
            db.session.query(func.min(Track.startTime), func.max(Track.startTime)
                             .filter(Track.user_id == current_user.id))
            .first())

        if minDate is None or maxDate is None:
            return None, None

        return minDate.year, maxDate.year

    @charts.route('/chartDistancePerCustomFieldChooser')
    @login_required
    def chartDistancePerCustomFieldChooser():
        return render_template('charts/chartDistancePerCustomFieldChooser.jinja2',
                               customFieldsByTrackType=get_custom_fields_by_track_type())

    @charts.route('/chartDistancePerCustomField/<string:track_type>/<string:name>')
    @login_required
    def chartDistancePerCustomField(track_type: str, name: str):
        trackType = TrackType(track_type)

        customField = Track.custom_fields[name].astext.cast(String)

        rows = (Track.query.with_entities(func.sum(Track.distance) / 1000, customField)
                .filter(Track.user_id == current_user.id)
                .filter(Track.type == trackType)
                .group_by(customField)
                .order_by(customField)
                .all())

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

        return render_template('charts/chartDistancePerCustomField.jinja2',
                               chartDistancePerCustomFieldData=chartDistancePerCustomFieldData,
                               customFieldName=name)

    @charts.route('/chartAverageSpeed')
    @login_required
    def chartAverageSpeed():
        minYear, maxYear = __get_min_and_max_year()

        chartDataAverageSpeed = []
        if minYear is None or maxYear is None:
            return chartDataAverageSpeed
        else:
            for trackType in TrackType:
                tracks = (Track.query
                          .filter(Track.user_id == current_user.id)
                          .filter(Track.type == trackType)
                          .order_by(Track.startTime.asc())
                          .all())

                dates = []
                speedData = []
                for track in tracks:
                    if track.duration is None:
                        continue

                    dates.append(track.startTime.strftime('%d.%m.%y'))
                    speedData.append(round(track.distance / track.duration * 3.6, 2))

                chartDataAverageSpeed.append({
                    'dates': dates,
                    'values': speedData,
                    'type': trackType
                })

        return render_template('charts/chartAverageSpeed.jinja2', chartDataAverageSpeed=chartDataAverageSpeed)

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
