import logging

from flask import Blueprint, abort, Response, send_file, send_from_directory
from flask_login import login_required

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

    @gpxTracks.route('/track/<int:track_id>')
    @login_required
    def downloadGpxTrackByTrackId(track_id: int):
        track = get_track_by_id(track_id)

        if track is None:
            abort(404)

        response = __downloadGpxTrack(gpxService, track, track.get_download_name())
        if response is not None:
            return response

        abort(404)

    @gpxTracks.route('/track/shared/<string:shareCode>')
    def downloadGpxTrackBySharedTrack(shareCode: str):
        track = get_track_by_share_code(shareCode)
        if track is None:
            abort(404)

        response = __downloadGpxTrack(gpxService, track, track.get_download_name())
        if response is not None:
            return response

        abort(404)

    @gpxTracks.route('/plannedTour/<int:tour_id>')
    @login_required
    def downloadGpxTrackByPlannedTourId(tour_id: int):
        plannedTour = get_planned_tour_by_id(tour_id)

        if plannedTour is None:
            abort(404)

        response = __downloadGpxTrack(gpxService, plannedTour, plannedTour.get_download_name())
        if response is not None:
            return response

        abort(404)

    @gpxTracks.route('/plannedTour/shared/<string:shareCode>')
    def downloadGpxTrackBySharedPlannedTour(shareCode: str):
        plannedTour = get_planned_tour_by_share_code(shareCode)

        if plannedTour is None:
            abort(404)

        response = __downloadGpxTrack(gpxService, plannedTour, plannedTour.get_download_name())
        if response is not None:
            return response

        abort(404)

    @gpxTracks.route('/delete/track/<int:track_id>')
    @login_required
    def deleteGpxTrackByTrackId(track_id: int):
        track = get_track_by_id(track_id)

        if track is None:
            return Response(status=204)

        gpxService.delete_gpx(track)
        return Response(status=204)

    @gpxTracks.route('/delete/plannedTour/<int:tour_id>')
    @login_required
    def deleteGpxTrackByPlannedTourId(tour_id: int):
        plannedTour = get_planned_tour_by_id(tour_id)

        if plannedTour is None:
            return Response(status=204)

        gpxService.delete_gpx(plannedTour)
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
