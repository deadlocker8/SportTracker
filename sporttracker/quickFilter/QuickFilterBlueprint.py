import logging
from datetime import datetime

from flask import Blueprint, redirect, request
from flask_login import login_required, current_user

from sporttracker import Constants
from sporttracker.helpers.DateFormats import DATE_FORMAT_DATE
from sporttracker.workout.WorkoutType import WorkoutType
from sporttracker.db import db
from sporttracker.quickFilter.QuickFilterStateEntity import get_quick_filter_state_by_user

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint():
    quickFilter = Blueprint('quickFilter', __name__, static_folder='static', url_prefix='/quickFilter')

    @quickFilter.route('/toggle/<string:workoutType>')
    @login_required
    def toggleQuickFilter(workoutType):
        redirectUrl = request.args['redirectUrl']

        workoutType = WorkoutType(workoutType)  # type: ignore[call-arg]

        quickFilterState = get_quick_filter_state_by_user(current_user.id)
        quickFilterState.toggle_workout_type(workoutType)
        db.session.commit()

        return redirect(redirectUrl)

    @quickFilter.route('/updateFilter', methods=['POST'])
    @login_required
    def updateFilter():
        filterMode = request.form.get('quickFilterMode')
        redirectUrl = request.form['redirectUrl']

        quickFilterState = get_quick_filter_state_by_user(current_user.id)

        if filterMode == 'years':
            activeYears = [int(item) for item in request.form.getlist('activeYears')]
            quickFilterState.update(quickFilterState.get_workout_types(), activeYears)
            quickFilterState.clear_date_filter()
        elif filterMode == 'dateRange':
            dateFrom = request.form.get('dateFrom', '')
            dateTo = request.form.get('dateTo', '')

            if not dateFrom and not dateTo:
                quickFilterState.clear_date_filter()
            elif dateFrom and dateTo:
                parsedDateFrom = datetime.strptime(dateFrom, DATE_FORMAT_DATE).date()
                parsedDateTo = datetime.strptime(dateTo, DATE_FORMAT_DATE).date()

                if parsedDateFrom <= parsedDateTo:
                    quickFilterState.set_date_filter(parsedDateFrom, parsedDateTo)
        else:
            return redirect(redirectUrl)

        db.session.commit()

        return redirect(redirectUrl)

    @quickFilter.route('/resetFilter', methods=['GET'])
    @login_required
    def resetFilter():
        redirectUrl = request.args['redirectUrl']

        quickFilterState = get_quick_filter_state_by_user(current_user.id)
        quickFilterState.update(quickFilterState.get_workout_types(), list(quickFilterState.get_years().keys()))
        quickFilterState.clear_date_filter()
        db.session.commit()

        return redirect(redirectUrl)

    return quickFilter
