import logging
from itertools import groupby

from flask import Blueprint, render_template, request
from flask_login import login_required, current_user

from logic import Constants
from logic.model.Track import Track
from logic.model.User import User

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint():
    search = Blueprint('search', __name__, static_folder='static', url_prefix='/search')

    @search.route('/search', methods=['POST'])
    @login_required
    def performSearch():
        searchText = request.form.get('searchText')

        if searchText is None:
            return render_template('search.jinja2', results={})

        searchText = searchText.strip()

        tracks = (Track.query.join(User)
                  .filter(User.username == current_user.username)
                  .filter(Track.name.icontains(searchText))
                  .order_by(Track.startTime.desc())
                  .all())

        results = {k: list(g) for k, g in groupby(tracks, key=lambda track: track.startTime.strftime('%B %Y'))}

        return render_template('search.jinja2',
                               results=results,
                               searchText=searchText,
                               numberOfResults=len(tracks))

    return search
