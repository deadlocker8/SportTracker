import logging

from flask import Blueprint, abort, Response, send_file, send_from_directory
from flask_login import login_required, current_user

from sporttracker.logic import Constants
from sporttracker.logic.GpxPreviewImageService import GpxPreviewImageService
from sporttracker.logic.GpxService import GpxService
from sporttracker.logic.model.PlannedTour import (
    get_planned_tour_by_id,
    get_planned_tour_by_share_code,
)
from sporttracker.logic.model.Track import get_track_by_id, get_track_by_share_code, Track

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint(gpxService: GpxService):
    gpxTracks = Blueprint('gpxTracks', __name__, static_folder='static', url_prefix='/gpxTracks')

    @gpxTracks.route('/track/<string:file_format>/<int:track_id>')
    @login_required
    def downloadGpxTrackByTrackId(track_id: int, file_format: str):
        track = get_track_by_id(track_id)

        if track is None:
            abort(404)

        response = __downloadTrackFile(gpxService, track, file_format)
        if response is not None:
            return response

        abort(404)

    @gpxTracks.route('/track/shared/<string:shareCode>/<string:file_format>')
    def downloadGpxTrackBySharedTrack(shareCode: str, file_format: str):
        track = get_track_by_share_code(shareCode)
        if track is None:
            abort(404)

        response = __downloadTrackFile(gpxService, track, file_format)
        if response is not None:
            return response

        abort(404)

    @gpxTracks.route('/plannedTour/<string:file_format>/<int:tour_id>')
    @login_required
    def downloadGpxTrackByPlannedTourId(tour_id: int, file_format: str):
        plannedTour = get_planned_tour_by_id(tour_id)

        if plannedTour is None:
            abort(404)

        response = __downloadTrackFile(gpxService, plannedTour, file_format)
        if response is not None:
            return response

        abort(404)

    @gpxTracks.route('/plannedTour/shared/<string:shareCode>/<string:file_format>')
    def downloadGpxTrackBySharedPlannedTour(shareCode: str, file_format: str):
        plannedTour = get_planned_tour_by_share_code(shareCode)

        if plannedTour is None:
            abort(404)

        response = __downloadTrackFile(gpxService, plannedTour, file_format)
        if response is not None:
            return response

        abort(404)

    @gpxTracks.route('/delete/track/<int:track_id>')
    @login_required
    def deleteGpxTrackByTrackId(track_id: int):
        track = get_track_by_id(track_id)

        if track is None:
            return Response(status=204)

        gpxService.delete_gpx(track, current_user.id)
        return Response(status=204)

    @gpxTracks.route('/delete/plannedTour/<int:tour_id>')
    @login_required
    def deleteGpxTrackByPlannedTourId(tour_id: int):
        plannedTour = get_planned_tour_by_id(tour_id)

        if plannedTour is None:
            return Response(status=204)

        gpxService.delete_gpx(plannedTour, current_user.id)
        return Response(status=204)

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

        gpxPreviewImageService = GpxPreviewImageService(gpxMetadata.gpx_file_name, gpxService)
        if not gpxPreviewImageService.is_image_existing():
            return send_from_directory(
                'static', path='images/map_placeholder.png', mimetype='image/png'
            )

        gpxPreviewImageFileName = gpxPreviewImageService.get_preview_image_path()
        return send_file(gpxPreviewImageFileName, mimetype='image/jpg')

    return gpxTracks


def __downloadTrackFile(gpxService: GpxService, item: Track, fileFormat: str) -> Response | None:
    if fileFormat == GpxService.GPX_FILE_EXTENSION:
        return __downloadGpxTrack(gpxService, item, item.get_download_name())
    elif fileFormat == GpxService.FIT_FILE_EXTENSION:
        return __downloadFitTrack(gpxService, item, item.get_download_name())

    return None


def __downloadGpxTrack(gpxService: GpxService, item: Track, downloadName: str) -> Response | None:
    gpxMetadata = item.get_gpx_metadata()
    if gpxMetadata is None:
        return None

    modifiedGpxXml = gpxService.get_joined_tracks_and_segments(gpxMetadata.gpx_file_name)
    fileName = f'{downloadName}.gpx'
    return Response(
        modifiedGpxXml,
        mimetype='application/gpx',
        headers={'content-disposition': f'attachment; filename={fileName}'},
    )


def __downloadFitTrack(gpxService: GpxService, item: Track, downloadName: str) -> Response | None:
    gpxMetadata = item.get_gpx_metadata()
    if gpxMetadata is None:
        return None

    fitContent = gpxService.get_fit_content(gpxMetadata.gpx_file_name)
    fileName = f'{downloadName}.fit'
    return Response(
        fitContent,
        mimetype='application/octet-stream',
        headers={'content-disposition': f'attachment; filename={fileName}'},
    )
