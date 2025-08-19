import logging

from flask import Blueprint, redirect, request
from flask_login import login_required, current_user

from sporttracker import Constants
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

    @quickFilter.route('/toggleYears', methods=['POST'])
    @login_required
    def toggleYears():
        activeYears = [int(item) for item in request.form.getlist('activeYears')]
        redirectUrl = request.form['redirectUrl']

        quickFilterState = get_quick_filter_state_by_user(current_user.id)
        quickFilterState.years = activeYears
        db.session.commit()

        return redirect(redirectUrl)

    return quickFilter
