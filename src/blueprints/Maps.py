import logging

from flask import Blueprint, render_template, abort, url_for
from flask_login import login_required, current_user

from logic import Constants
from logic.model.Track import Track, TrackType
from logic.model.User import User

LOGGER = logging.getLogger(Constants.APP_NAME)


def createGpxInfo(track: Track) -> dict[str, str]:
    return {
        'gpxUrl': url_for('gpxTracks.downloadGpxTrack', track_id=track.id, _external=True),
        'trackUrl': url_for('tracks.edit', track_id=track.id, _external=True),
        'trackName': f'{track.startTime.strftime("%Y-%m-%d")} - {track.name}'
    }


def construct_blueprint():
    maps = Blueprint('maps', __name__, static_folder='static')

    @maps.route('/map')
    @login_required
    def showAllTracksOnMap():
        gpxInfo = []

        for trackType in TrackType:
            tracks = (Track.query
                      .filter(Track.user_id == current_user.id)
                      .filter(Track.type == trackType)
                      .filter(Track.gpxFileName.isnot(None))
                      .order_by(Track.startTime.asc())
                      .all())

            for track in tracks:
                gpxInfo.append(createGpxInfo(track))

        # TODO: grop by TrackType
        return render_template('map.jinja2', gpxInfo=gpxInfo)

    @maps.route('/map/<int:track_id>')
    @login_required
    def showSingleTrack(track_id: int):
        track: Track | None = (Track.query.join(User)
                               .filter(User.username == current_user.username)
                               .filter(Track.id == track_id)
                               .first())

        if track is None:
            abort(404)

        gpxInfo = []
        if track.gpxFileName:
            gpxInfo = [createGpxInfo(track)]

        return render_template('map.jinja2', gpxInfo=gpxInfo)

    return maps
