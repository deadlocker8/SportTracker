import logging

from flask import Blueprint, render_template, abort, url_for
from flask_login import login_required, current_user

from logic import Constants
from logic.model.Track import Track, TrackType
from logic.model.User import User

LOGGER = logging.getLogger(Constants.APP_NAME)


def createGpxInfo(track: Track) -> dict[str, str]:
    return {
        'gpxUrl': 'http://localhost:10022/static/gpx/2023-04-22_Nossen.gpx',
        'trackUrl': url_for('tracks.edit', track_id=track.id, _external=True),
        'trackName': track.name
    }


def construct_blueprint():
    maps = Blueprint('maps', __name__, static_folder='static')

    @maps.route('/map')
    @login_required
    def showAllTracksOnMap():

        for trackType in TrackType:
            tracks = (Track.query
                      .filter(Track.user_id == current_user.id)
                      .filter(Track.type == trackType)
                      .order_by(Track.startTime.asc())
                      .all())

        # TODO: grop by TrackType
        return render_template('map.jinja2', gpxInfo=[])

    @maps.route('/map/<int:track_id>')
    @login_required
    def showSingleTrack(track_id: int):
        track: Track | None = (Track.query.join(User)
                               .filter(User.username == current_user.username)
                               .filter(Track.id == track_id)
                               .first())

        if track is None:
            abort(404)

        # TODO: get gpx from track
        gpxInfo = []
        if track.gpx:
            gpxInfo = [createGpxInfo(track)]

        return render_template('map.jinja2', gpxInfo=gpxInfo)

    return maps
