import logging

from flask import Blueprint, redirect, request
from flask_login import login_required, current_user

from sporttracker.logic import Constants
from sporttracker.logic.model.WorkoutType import WorkoutType
from sporttracker.logic.model.db import db
from sporttracker.logic.model.filterStates.QuickFilterState import get_quick_filter_state_by_user

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

    return quickFilter
