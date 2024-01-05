import logging

from flask import Blueprint, send_from_directory, abort
from flask_login import login_required, current_user

from logic import Constants
from logic.model.Track import Track
from logic.model.User import User

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint(uploadFolder: str):
    gpxTracks = Blueprint('gpxTracks', __name__, static_folder='static')

    @gpxTracks.route('/<int:track_id>')
    @login_required
    def downloadGpxTrack(track_id: int):
        track: Track | None = (Track.query.join(User)
                               .filter(User.username == current_user.username)
                               .filter(Track.id == track_id)
                               .first())

        if track is None:
            abort(404)

        if track.gpxFileName is not None:
            return send_from_directory(uploadFolder, str(track.gpxFileName), as_attachment=True)

        abort(404)

    return gpxTracks
