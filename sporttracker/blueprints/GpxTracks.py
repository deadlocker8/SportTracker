import logging
import os
import uuid

from flask import Blueprint, abort, Response
from flask_login import login_required
from werkzeug.datastructures.file_storage import FileStorage

from sporttracker.logic import Constants
from sporttracker.logic.GpxService import GpxService
from sporttracker.logic.model.PlannedTour import get_planned_tour_by_id
from sporttracker.logic.model.Track import get_track_by_id
from sporttracker.logic.model.db import db

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint(uploadFolder: str):
    gpxTracks = Blueprint('gpxTracks', __name__, static_folder='static', url_prefix='/gpxTracks')

    @gpxTracks.route('/track/<int:track_id>')
    @login_required
    def downloadGpxTrackByTrackId(track_id: int):
        track = get_track_by_id(track_id)

        if track is None:
            abort(404)

        response = __downloadGpxTrack(uploadFolder, track, str(track.id))
        if response is not None:
            return response

        abort(404)

    @gpxTracks.route('/plannedTour<int:tour_id>')
    @login_required
    def downloadGpxTrackByPlannedTourId(tour_id: int):
        plannedTour = get_planned_tour_by_id(tour_id)

        if plannedTour is None:
            abort(404)

        downloadFileName = ''.join([c if c.isalnum() else '_' for c in str(plannedTour.name)])
        response = __downloadGpxTrack(uploadFolder, plannedTour, downloadFileName)
        if response is not None:
            return response

        abort(404)

    @gpxTracks.route('/delete/track/<int:track_id>')
    @login_required
    def deleteGpxTrackByTrackId(track_id: int):
        track = get_track_by_id(track_id)

        if track is None:
            return Response(status=204)

        return __deleteGpxTrack(uploadFolder, track)

    @gpxTracks.route('/delete/plannedTour/<int:tour_id>')
    @login_required
    def deleteGpxTrackByPlannedTourId(tour_id: int):
        plannedTour = get_planned_tour_by_id(tour_id)

        if plannedTour is None:
            return Response(status=204)

        return __deleteGpxTrack(uploadFolder, plannedTour)

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


def __downloadGpxTrack(uploadFolder: str, item, downloadName: str) -> Response | None:
    if item.gpxFileName is not None:
        gpxTrackPath = os.path.join(uploadFolder, str(item.gpxFileName))
        gpxService = GpxService(gpxTrackPath)
        modifiedGpxXml = gpxService.join_tracks_and_segments()
        fileName = f'{downloadName}.gpx'
        return Response(
            modifiedGpxXml,
            mimetype='application/gpx',
            headers={'content-disposition': f'attachment; filename={fileName}'},
        )

    return None


def __deleteGpxTrack(uploadFolder: str, item) -> Response:
    gpxFileName = str(item.gpxFileName)
    if gpxFileName is not None:
        item.gpxFileName = None  # type: ignore[assignment]
        db.session.commit()

        try:
            os.remove(os.path.join(uploadFolder, gpxFileName))
            LOGGER.debug(
                f'Deleted linked gpx file "{gpxFileName}" for {item.__class__.__name__} id {item.id}'
            )
        except OSError as e:
            LOGGER.error(e)

    return Response(status=204)
