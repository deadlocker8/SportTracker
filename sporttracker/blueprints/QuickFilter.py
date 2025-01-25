import logging

from flask import Blueprint, session, redirect, request
from flask_login import login_required

from sporttracker.logic import Constants
from sporttracker.logic.QuickFilterState import get_quick_filter_state_from_session
from sporttracker.logic.model.SportType import SportType

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint():
    quickFilter = Blueprint(
        'quickFilter', __name__, static_folder='static', url_prefix='/quickFilter'
    )

    @quickFilter.route('/toggle/<string:sportType>')
    @login_required
    def toggleQuickFilter(sportType):
        redirectUrl = request.args['redirectUrl']

        sportType = SportType(sportType)  # type: ignore[call-arg]

        quickFilterState = get_quick_filter_state_from_session()
        quickFilterState.toggle_state(sportType)
        session['quickFilterState'] = quickFilterState.to_json()

        return redirect(redirectUrl)

    return quickFilter
