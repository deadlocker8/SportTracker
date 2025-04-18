import logging

from flask import Blueprint, session, redirect, request
from flask_login import login_required

from sporttracker.logic import Constants
from sporttracker.logic.QuickFilterState import get_quick_filter_state_from_session
from sporttracker.logic.model.WorkoutType import WorkoutType

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint():
    quickFilter = Blueprint('quickFilter', __name__, static_folder='static', url_prefix='/quickFilter')

    @quickFilter.route('/toggle/<string:workoutType>')
    @login_required
    def toggleQuickFilter(workoutType):
        redirectUrl = request.args['redirectUrl']

        workoutType = WorkoutType(workoutType)  # type: ignore[call-arg]

        quickFilterState = get_quick_filter_state_from_session()
        quickFilterState.toggle_state(workoutType)
        session['quickFilterState'] = quickFilterState.to_json()

        return redirect(redirectUrl)

    return quickFilter
