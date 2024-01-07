import logging
from datetime import datetime

from flask import Blueprint, render_template, abort, url_for
from flask_login import login_required, current_user
from sqlalchemy import func

from logic import Constants
from logic.model.Track import Track, TrackType
from logic.model.User import User

LOGGER = logging.getLogger(Constants.APP_NAME)


def createGpxInfo(trackId: int, trackName: str, trackStartTime: datetime) -> dict[str, str]:
    return {
        'gpxUrl': url_for('gpxTracks.downloadGpxTrack', track_id=trackId, _external=True),
        'trackUrl': url_for('tracks.edit', track_id=trackId, _external=True),
        'trackName': f'{trackStartTime.strftime("%Y-%m-%d")} - {trackName}'
    }


def construct_blueprint():
    maps = Blueprint('maps', __name__, static_folder='static')

    @maps.route('/map')
    @login_required
    def showAllTracksOnMap():
        gpxInfo = []

        funcStartTime = func.max(Track.startTime)
        for trackType in TrackType:
            tracks = (Track.query.with_entities(func.max(Track.id), Track.name, funcStartTime)
                      .filter(Track.user_id == current_user.id)
                      .filter(Track.type == trackType)
                      .filter(Track.gpxFileName.isnot(None))
                      .group_by(Track.name)
                      .order_by(funcStartTime.desc())
                      .all())

            for track in tracks:
                trackId, trackName, trackStartTime = track
                gpxInfo.append(createGpxInfo(trackId, trackName, trackStartTime))

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
            gpxInfo = [createGpxInfo(track.id, track.name, track.startTime)]

        return render_template('map.jinja2', gpxInfo=gpxInfo)

    return maps
