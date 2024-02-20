import logging
from itertools import groupby

from flask import Blueprint, render_template, request
from flask_login import login_required, current_user

from logic import Constants
from logic.model.Track import Track
from logic.model.User import User
from logic.model.db import db

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint():
    search = Blueprint('search', __name__, static_folder='static', url_prefix='/search')

    @search.route('/search')
    @login_required
    def performSearch():
        searchText = request.args.get('searchText')
        pageNumber = request.args.get('pageNumber')

        if searchText is None:
            return render_template('search.jinja2', results={})

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
            .order_by(Track.startTime.desc()),
            per_page=10,
            page=pageNumberValue,
        )

        results = {
            k: list(g)
            for k, g in groupby(
                pagination.items, key=lambda track: track.startTime.strftime('%B %Y')
            )
        }

        return render_template(
            'search.jinja2',
            results=results,
            pagination=pagination,
            searchText=searchText,
        )

    return search
