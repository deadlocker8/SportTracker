import logging
import os
import uuid
from typing import Any

from flask import Blueprint, abort, Response, send_file, send_from_directory
from flask_login import login_required
from werkzeug.datastructures.file_storage import FileStorage

from sporttracker.logic import Constants
from sporttracker.logic.GpxPreviewImageService import GpxPreviewImageService
from sporttracker.logic.GpxService import GpxService
from sporttracker.logic.model.GpxMetadata import GpxMetadata
from sporttracker.logic.model.PlannedTour import (
    get_planned_tour_by_id,
    get_planned_tour_by_share_code,
    PlannedTour,
)
from sporttracker.logic.model.Track import get_track_by_id, get_track_by_share_code, Track
from sporttracker.logic.model.db import db

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint(uploadFolder: str, baseZoomLevel: int):
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

    @gpxTracks.route('/track/shared/<string:shareCode>')
    def downloadGpxTrackBySharedTrack(shareCode: str):
        track = get_track_by_share_code(shareCode)
        if track is None:
            abort(404)

        response = __downloadGpxTrack(uploadFolder, track, str(track.id))
        if response is not None:
            return response

        abort(404)

    @gpxTracks.route('/plannedTour/<int:tour_id>')
    @login_required
    def downloadGpxTrackByPlannedTourId(tour_id: int):
        plannedTour = get_planned_tour_by_id(tour_id)

        if plannedTour is None:
            abort(404)

        response = __downloadGpxTrack(uploadFolder, plannedTour, plannedTour.get_download_name())
        if response is not None:
            return response

        abort(404)

    @gpxTracks.route('/plannedTour/shared/<string:shareCode>')
    def downloadGpxTrackBySharedPlannedTour(shareCode: str):
        plannedTour = get_planned_tour_by_share_code(shareCode)

        if plannedTour is None:
            abort(404)

        response = __downloadGpxTrack(uploadFolder, plannedTour, plannedTour.get_download_name())
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

    @gpxTracks.route('/previewImage<int:tour_id>')
    @login_required
    def getPreviewImageByPlannedTourId(tour_id: int):
        plannedTour = get_planned_tour_by_id(tour_id)

        if plannedTour is None:
            abort(404)

        gpxMetadata = plannedTour.get_gpx_metadata()
        if gpxMetadata is None:
            return send_from_directory(
                'static', path='images/map_placeholder.png', mimetype='image/png'
            )

        gpxPreviewImageService = GpxPreviewImageService(gpxMetadata.gpx_file_name, uploadFolder)
        if not gpxPreviewImageService.is_image_existing():
            return send_from_directory(
                'static', path='images/map_placeholder.png', mimetype='image/png'
            )

        gpxPreviewImageFileName = gpxPreviewImageService.get_preview_image_path()
        return send_file(gpxPreviewImageFileName, mimetype='image/jpg')

    return gpxTracks


def __is_allowed_file(filename: str) -> bool:
    if '.' not in filename:
        return False

    return filename.rsplit('.', 1)[1].lower() == 'gpx'


def handleGpxTrackForTrack(files: dict[str, FileStorage], uploadFolder: str) -> int | None:
    gpxFileName = __handleGpxTrack(files, uploadFolder, False, {})
    if gpxFileName is None:
        return None

    return __create_gpx_metadata(gpxFileName, uploadFolder)


def handleGpxTrackForPlannedTour(
    files: dict[str, FileStorage], uploadFolder: str, gpxPreviewImageSettings: dict[str, Any]
) -> int | None:
    gpxFileName = __handleGpxTrack(
        files, uploadFolder, gpxPreviewImageSettings['enabled'], gpxPreviewImageSettings
    )
    if gpxFileName is None:
        return None

    return __create_gpx_metadata(gpxFileName, uploadFolder)


def __handleGpxTrack(
    files: dict[str, FileStorage],
    uploadFolder: str,
    generatePreviewImage: bool,
    gpxPreviewImageSettings: dict[str, Any],
) -> str | None:
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

        if generatePreviewImage:
            gpxPreviewImageService = GpxPreviewImageService(filename, uploadFolder)
            gpxPreviewImagePath = gpxPreviewImageService.get_preview_image_path()
            gpxPreviewImageService.generate_image(gpxPreviewImageSettings)
            LOGGER.debug(f'Generated gpx preview image {gpxPreviewImagePath}')

        return filename

    return None


def __create_gpx_metadata(gpxFileName: str, uploadFolder: str) -> int:
    gpxTrackPath = os.path.join(uploadFolder, str(gpxFileName))
    # TODO
    gpxService = GpxService(gpxTrackPath, 0, (0, 0, 0, 0))
    metaInfo = gpxService.get_meta_info()

    gpxMetadata = GpxMetadata(
        gpx_file_name=gpxFileName,
        length=metaInfo.distance,
        elevation_minimum=metaInfo.elevationExtremes.minimum,
        elevation_maximum=metaInfo.elevationExtremes.maximum,
        uphill=metaInfo.uphillDownhill.uphill,
        downhill=metaInfo.uphillDownhill.downhill,
    )

    LOGGER.debug(f'Saved new gpxMetadata: {gpxMetadata}')
    db.session.add(gpxMetadata)
    db.session.commit()

    return gpxMetadata.id


def __downloadGpxTrack(uploadFolder: str, item: Track, downloadName: str) -> Response | None:
    gpxMetadata = item.get_gpx_metadata()
    if gpxMetadata is None:
        return None

    gpxTrackPath = os.path.join(uploadFolder, gpxMetadata.gpx_file_name)
    # TODO:
    gpxService = GpxService(gpxTrackPath, 0, (0, 0, 0, 0))
    modifiedGpxXml = gpxService.join_tracks_and_segments()
    fileName = f'{downloadName}.gpx'
    return Response(
        modifiedGpxXml,
        mimetype='application/gpx',
        headers={'content-disposition': f'attachment; filename={fileName}'},
    )


def __deleteGpxTrack(uploadFolder: str, item: Track | PlannedTour) -> Response:
    gpxMetadata = item.get_gpx_metadata()
    if gpxMetadata is not None:
        item.gpx_metadata_id = None
        db.session.delete(gpxMetadata)
        db.session.commit()

        try:
            os.remove(os.path.join(uploadFolder, gpxMetadata.gpx_file_name))
            LOGGER.debug(
                f'Deleted linked gpx file "{gpxMetadata.gpx_file_name}" for {item.__class__.__name__} id {item.id}'
            )
        except OSError as e:
            LOGGER.error(e)

        gpxPreviewImageService = GpxPreviewImageService(gpxMetadata.gpx_file_name, uploadFolder)
        gpxPreviewImagePath = gpxPreviewImageService.get_preview_image_path()
        if gpxPreviewImageService.is_image_existing():
            try:
                os.remove(gpxPreviewImagePath)
                LOGGER.debug(
                    f'Deleted preview image file "{gpxPreviewImagePath}" for {item.__class__.__name__} id {item.id}'
                )
            except OSError as e:
                LOGGER.error(e)

    return Response(status=204)
