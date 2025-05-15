import logging
from typing import Any

from flask import Blueprint, render_template, Response
from flask_login import login_required

from sporttracker.logic import Constants
from sporttracker.logic.GpxService import GpxService
from sporttracker.logic.QuickFilterState import get_quick_filter_state_from_session

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint(gpxService: GpxService, gpxPreviewImageSettings: dict[str, Any]) -> Blueprint:
    longDistanceTours = Blueprint(
        'longDistanceTours', __name__, static_folder='static', url_prefix='/longDistanceTours'
    )

    @longDistanceTours.route('/')
    @login_required
    def listLongDistanceTours():
        quickFilterState = get_quick_filter_state_from_session()

        return render_template(
            'longDistanceTours/longDistanceTours.jinja2',
            longDistanceTours=[],
            quickFilterState=quickFilterState,
            isGpxPreviewImagesEnabled=gpxPreviewImageSettings['enabled'],
        )

    @longDistanceTours.route('/setLastViewedDate')
    @login_required
    def set_last_viewed_date():
        # user = User.query.filter(User.id == current_user.id).first()
        # user.planned_tours_last_viewed_date = datetime.now()
        # db.session.commit()

        return Response(status=204)

    return longDistanceTours
