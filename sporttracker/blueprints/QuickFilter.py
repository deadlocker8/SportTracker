import logging

from flask import Blueprint, session, redirect, request
from flask_login import login_required

from sporttracker.logic import Constants
from sporttracker.logic.QuickFilterState import get_quick_filter_state_from_session
from sporttracker.logic.model.TrackType import TrackType

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint():
    quickFilter = Blueprint(
        'quickFilter', __name__, static_folder='static', url_prefix='/quickFilter'
    )

    @quickFilter.route('/toggle/<string:trackType>')
    @login_required
    def toggleQuickFilter(trackType):
        redirectUrl = request.args['redirectUrl']

        trackType = TrackType(trackType)  # type: ignore[call-arg]

        quickFilterState = get_quick_filter_state_from_session()
        quickFilterState.toggle_state(trackType)
        session['quickFilterState'] = quickFilterState.to_json()

        return redirect(redirectUrl)

    return quickFilter
