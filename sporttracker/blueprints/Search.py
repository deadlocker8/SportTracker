import logging
from itertools import groupby

from flask import Blueprint, render_template, request
from flask_babel import format_datetime
from flask_login import login_required, current_user

from sporttracker.blueprints.Tracks import TrackModel
from sporttracker.logic import Constants
from sporttracker.logic.QuickFilterState import get_quick_filter_state_from_session
from sporttracker.logic.model.Track import Track
from sporttracker.logic.model.User import User
from sporttracker.logic.model.db import db

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint():
    search = Blueprint('search', __name__, static_folder='static', url_prefix='/search')

    @search.route('/search')
    @login_required
    def performSearch():
        searchText = request.args.get('searchText')
        pageNumber = request.args.get('pageNumber')

        quickFilterState = get_quick_filter_state_from_session()

        if searchText is None:
            return render_template(
                'search.jinja2',
                results={},
                quickFilterState=quickFilterState,
            )

        searchText = searchText.strip()

        try:
            pageNumberValue = int(pageNumber)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            pageNumberValue = 1

        if pageNumberValue < 1:
            pageNumberValue = 1

        pagination = db.paginate(
            Track.query.join(User)
            .filter(User.username == current_user.username)
            .filter(Track.name.icontains(searchText))
            .filter(Track.type.in_(quickFilterState.get_active_types()))
            .order_by(Track.startTime.desc()),
            per_page=10,
            page=pageNumberValue,
        )

        results = {
            k: list(g)
            for k, g in groupby(
                pagination.items,
                key=lambda track: format_datetime(track.startTime, format='MMMM yyyy'),
            )
        }

        resultModelItems = {}
        for month, tracks in results.items():
            resultModelItems[month] = [TrackModel.create_from_track(t) for t in tracks]

        return render_template(
            'search.jinja2',
            results=resultModelItems,
            pagination=pagination,
            searchText=searchText,
            quickFilterState=quickFilterState,
        )

    return search
