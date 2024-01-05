import logging
import os

from flask import Blueprint, send_from_directory, abort, redirect, url_for
from flask_login import login_required, current_user

from logic import Constants
from logic.model.Track import Track
from logic.model.User import User
from logic.model.db import db

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint(uploadFolder: str):
    gpxTracks = Blueprint('gpxTracks', __name__, static_folder='static', url_prefix='/gpxTracks')

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

    @gpxTracks.route('/delete/<int:track_id>')
    @login_required
    def deleteGpxTrack(track_id: int):
        track: Track | None = (Track.query.join(User)
                               .filter(User.username == current_user.username)
                               .filter(Track.id == track_id)
                               .first())

        if track is None:
            return redirect(url_for('tracks.edit', track_id=track_id))

        if track.gpxFileName is not None:
            track.gpxFileName = None
            db.session.commit()

            try:
                os.remove(os.path.join(uploadFolder, str(track.gpxFileName)))
                LOGGER.debug(f'Deleted linked gpx file "{track.gpxFileName}" for track with id {track_id}')
            except OSError as e:
                LOGGER.error(e)

        return redirect(url_for('tracks.edit', track_id=track_id))

    return gpxTracks
