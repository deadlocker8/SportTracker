import logging
from typing import Any

from flask import Blueprint, abort, Response, send_file, send_from_directory
from flask_login import login_required, current_user

from sporttracker.logic import Constants
from sporttracker.gpx.GpxPreviewImageService import GpxPreviewImageService
from sporttracker.gpx.GpxService import GpxService
from sporttracker.gpx.LongDistanceTourGpxPreviewImageService import LongDistanceTourGpxPreviewImageService
from sporttracker.workout.distance.DistanceWorkoutEntity import DistanceWorkout
from sporttracker.workout.distance.DistanceWorkoutService import DistanceWorkoutService
from sporttracker.longDistanceTour.LongDistanceTourService import LongDistanceTourService
from sporttracker.plannedTour.PlannedTourService import PlannedTourService

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint(
    gpxService: GpxService, distanceWorkoutService: DistanceWorkoutService, gpxPreviewSettings: dict[str, Any]
):
    gpxTracks = Blueprint('gpxTracks', __name__, static_folder='static', url_prefix='/gpxTracks')

    @gpxTracks.route('/workout/<string:file_format>/<int:workout_id>')
    @login_required
    def downloadGpxTrackByWorkoutId(workout_id: int, file_format: str):
        workout = distanceWorkoutService.get_distance_workout_by_id(workout_id, current_user.id)

        if workout is None:
            abort(404)

        response = __downloadTrackFile(gpxService, workout, file_format)
        if response is not None:
            return response

        abort(404)

    @gpxTracks.route('/workout/shared/<string:shareCode>/<string:file_format>')
    def downloadGpxTrackBySharedWorkout(shareCode: str, file_format: str):
        workout = distanceWorkoutService.get_distance_workout_by_share_code(shareCode)
        if workout is None:
            abort(404)

        response = __downloadTrackFile(gpxService, workout, file_format)
        if response is not None:
            return response

        abort(404)

    @gpxTracks.route('/plannedTour/<string:file_format>/<int:tour_id>')
    @login_required
    def downloadGpxTrackByPlannedTourId(tour_id: int, file_format: str):
        plannedTour = PlannedTourService.get_planned_tour_by_id(tour_id)

        if plannedTour is None:
            abort(404)

        response = __downloadTrackFile(gpxService, plannedTour, file_format)
        if response is not None:
            return response

        abort(404)

    @gpxTracks.route('/plannedTour/shared/<string:shareCode>/<string:file_format>')
    def downloadGpxTrackBySharedPlannedTour(shareCode: str, file_format: str):
        plannedTour = PlannedTourService.get_planned_tour_by_share_code(shareCode)

        if plannedTour is None:
            abort(404)

        response = __downloadTrackFile(gpxService, plannedTour, file_format)
        if response is not None:
            return response

        abort(404)

    @gpxTracks.route('/delete/workout/<int:workout_id>')
    @login_required
    def deleteGpxTrackByWorkoutId(workout_id: int):
        workout = distanceWorkoutService.get_distance_workout_by_id(workout_id, current_user.id)

        if workout is None:
            return Response(status=204)

        gpxService.delete_gpx(workout, current_user.id)
        return Response(status=204)

    @gpxTracks.route('/delete/plannedTour/<int:tour_id>')
    @login_required
    def deleteGpxTrackByPlannedTourId(tour_id: int):
        plannedTour = PlannedTourService.get_planned_tour_by_id(tour_id)

        if plannedTour is None:
            return Response(status=204)

        gpxService.delete_gpx(plannedTour, current_user.id)
        return Response(status=204)

    @gpxTracks.route('/previewImage/<int:tour_id>')
    @login_required
    def getPreviewImageByPlannedTourId(tour_id: int):
        plannedTour = PlannedTourService.get_planned_tour_by_id(tour_id)

        if plannedTour is None:
            abort(404)

        gpxMetadata = plannedTour.get_gpx_metadata()
        if gpxMetadata is None:
            return send_from_directory('static', path='images/map_placeholder.png', mimetype='image/png')

        gpxPreviewImageService = GpxPreviewImageService(gpxMetadata.gpx_file_name, gpxService)
        if not gpxPreviewImageService.is_image_existing():
            return send_from_directory('static', path='images/map_placeholder.png', mimetype='image/png')

        gpxPreviewImageFileName = gpxPreviewImageService.get_preview_image_path()
        return send_file(gpxPreviewImageFileName, mimetype='image/jpg')

    @gpxTracks.route('/previewImage/longDistanceTour/<int:tour_id>')
    @login_required
    def getPreviewImageByLongDistanceTourId(tour_id: int):
        longDistanceTour = LongDistanceTourService.get_long_distance_tour_by_id(tour_id)

        if longDistanceTour is None:
            abort(404)

        gpxPreviewImageService = LongDistanceTourGpxPreviewImageService(longDistanceTour, gpxService)

        if not gpxPreviewImageService.is_image_existing():
            return send_from_directory('static', path='images/map_placeholder.png', mimetype='image/png')

        gpxPreviewImageFileName = gpxPreviewImageService.get_preview_image_path()
        return send_file(gpxPreviewImageFileName, mimetype='image/jpg')

    return gpxTracks


def __downloadTrackFile(gpxService: GpxService, item: DistanceWorkout, fileFormat: str) -> Response | None:
    if fileFormat == GpxService.GPX_FILE_EXTENSION:
        return __downloadGpxTrack(gpxService, item, item.get_download_name())
    elif fileFormat == GpxService.FIT_FILE_EXTENSION:
        return __downloadFitTrack(gpxService, item, item.get_download_name())

    return None


def __downloadGpxTrack(gpxService: GpxService, item: DistanceWorkout, downloadName: str) -> Response | None:
    gpxMetadata = item.get_gpx_metadata()
    if gpxMetadata is None:
        return None

    modifiedGpxXml = gpxService.get_joined_tracks_and_segments(gpxMetadata.gpx_file_name, downloadName)
    fileName = f'{downloadName}.gpx'
    return Response(
        modifiedGpxXml,
        mimetype='application/gpx',
        headers={'content-disposition': f'attachment; filename={fileName}'},
    )


def __downloadFitTrack(gpxService: GpxService, item: DistanceWorkout, downloadName: str) -> Response | None:
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
