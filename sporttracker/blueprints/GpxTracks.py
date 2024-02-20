import logging
import os
import uuid

from flask import Blueprint, abort, Response
from flask_login import login_required, current_user
from werkzeug.datastructures.file_storage import FileStorage

from sporttracker.logic import Constants
from sporttracker.logic.GpxService import GpxService
from sporttracker.logic.model.Track import Track
from sporttracker.logic.model.User import User
from sporttracker.logic.model.db import db

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint(uploadFolder: str):
    gpxTracks = Blueprint('gpxTracks', __name__, static_folder='static', url_prefix='/gpxTracks')

    @gpxTracks.route('/<int:track_id>')
    @login_required
    def downloadGpxTrack(track_id: int):
        track: Track | None = (
            Track.query.join(User)
            .filter(User.username == current_user.username)
            .filter(Track.id == track_id)
            .first()
        )

        if track is None:
            abort(404)

        if track.gpxFileName is not None:
            gpxTrackPath = os.path.join(uploadFolder, str(track.gpxFileName))
            gpxService = GpxService(gpxTrackPath)
            modifiedGpxXml = gpxService.join_tracks_and_segments()
            fileName = f'{track_id}.gpx'
            return Response(
                modifiedGpxXml,
                mimetype='application/gpx',
                headers={'content-disposition': f'attachment; filename={fileName}'},
            )

        abort(404)

    @gpxTracks.route('/delete/<int:track_id>')
    @login_required
    def deleteGpxTrack(track_id: int):
        track: Track | None = (
            Track.query.join(User)
            .filter(User.username == current_user.username)
            .filter(Track.id == track_id)
            .first()
        )

        if track is None:
            return Response(status=204)

        gpxFileName = str(track.gpxFileName)
        if gpxFileName is not None:
            track.gpxFileName = None  # type: ignore[assignment]
            db.session.commit()

            try:
                os.remove(os.path.join(uploadFolder, gpxFileName))
                LOGGER.debug(
                    f'Deleted linked gpx file "{gpxFileName}" for track with id {track_id}'
                )
            except OSError as e:
                LOGGER.error(e)

        return Response(status=204)

    return gpxTracks


def __is_allowed_file(filename: str) -> bool:
    if '.' not in filename:
        return False

    return filename.rsplit('.', 1)[1].lower() == 'gpx'


def handleGpxTrack(files: dict[str, FileStorage], uploadFolder: str) -> str | None:
    if 'gpxTrack' not in files:
        return None

    file = files['gpxTrack']
    if file.filename == '' or file.filename is None:
        return None

    if file and __is_allowed_file(file.filename):
        filename = f'{uuid.uuid4().hex}.gpx'
        destinationPath = os.path.join(uploadFolder, filename)
        file.save(destinationPath)
        LOGGER.debug(f'Saved uploaded file {file.filename} to {destinationPath}')
        return filename

    return None
