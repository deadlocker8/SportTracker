import io
import logging
import os
from datetime import datetime
from typing import Any

from PIL import ImageColor
from flask import Blueprint, render_template, abort, url_for, session, redirect, request, Response
from flask_login import login_required, current_user
from sqlalchemy import func, extract, or_

from sporttracker.blueprints.PlannedTours import PlannedTourModel
from sporttracker.blueprints.Tracks import TrackModel
from sporttracker.logic import Constants
from sporttracker.logic.GpxService import CachedGpxService
from sporttracker.logic.QuickFilterState import get_quick_filter_state_from_session
from sporttracker.logic.TileRenderService import TileRenderService
from sporttracker.logic.VisitedTileService import VisitedTileService
from sporttracker.logic.model.PlannedTour import (
    get_planned_tour_by_id,
    PlannedTour,
    get_planned_tour_by_share_code,
)
from sporttracker.logic.model.Track import (
    Track,
    get_available_years,
    get_track_by_id,
    get_track_by_share_code,
)

LOGGER = logging.getLogger(Constants.APP_NAME)


def createGpxInfo(trackId: int, trackName: str, trackStartTime: datetime) -> dict[str, str | int]:
    return {
        'trackId': trackId,
        'gpxUrl': url_for('gpxTracks.downloadGpxTrackByTrackId', track_id=trackId),
        'trackUrl': url_for('tracks.edit', track_id=trackId),
        'trackName': f'{trackStartTime.strftime("%Y-%m-%d")} - {trackName}',
    }


def createGpxInfoPlannedTour(tourId: int, tourName: str) -> dict[str, str | int]:
    return {
        'trackId': tourId,
        'gpxUrl': url_for('gpxTracks.downloadGpxTrackByPlannedTourId', tour_id=tourId),
        'trackUrl': url_for('plannedTours.edit', tour_id=tourId),
        'trackName': tourName,
    }


def construct_blueprint(
    uploadFolder: str, cachedGpxService: CachedGpxService, tileHuntingSettings: dict[str, Any]
):
    maps = Blueprint('maps', __name__, static_folder='static')

    @maps.route('/map')
    @login_required
    def showAllTracksOnMap():
        quickFilterState = get_quick_filter_state_from_session()
        availableYears = get_available_years()
        yearFilterState = __get_map_year_filter_state_from_session(availableYears)

        gpxInfo = []

        funcStartTime = func.max(Track.startTime)
        tracks = (
            Track.query.with_entities(func.max(Track.id), Track.name, funcStartTime)
            .filter(Track.user_id == current_user.id)
            .filter(Track.gpx_metadata_id.isnot(None))
            .filter(Track.type.in_(quickFilterState.get_active_types()))
            .filter(extract('year', Track.startTime).in_(yearFilterState))
            .group_by(Track.name)
            .order_by(funcStartTime.desc())
            .all()
        )

        for track in tracks:
            trackId, trackName, trackStartTime = track
            gpxInfo.append(createGpxInfo(trackId, trackName, trackStartTime))

        return render_template(
            'maps/mapMultipleTracks.jinja2',
            gpxInfo=gpxInfo,
            quickFilterState=quickFilterState,
            yearFilterState=yearFilterState,
            availableYears=availableYears,
            mapMode='tracks',
            redirectUrl='maps.showAllTracksOnMap',
        )

    @maps.route('/map/<int:track_id>')
    @login_required
    def showSingleTrack(track_id: int):
        track = get_track_by_id(track_id)

        if track is None:
            abort(404)

        tileRenderUrl = url_for(
            'maps.renderTile',
            track_id=track_id,
            user_id=current_user.id,
            zoom=0,
            x=0,
            y=0,
            _external=True,
        )
        tileRenderUrl = tileRenderUrl.split('/0/0/0')[0]

        return render_template(
            'maps/mapSingleTrack.jinja2',
            track=TrackModel.create_from_track(track),
            gpxUrl=url_for('gpxTracks.downloadGpxTrackByTrackId', track_id=track_id),
            editUrl=url_for('tracks.edit', track_id=track_id),
            tileRenderUrl=tileRenderUrl,
        )

    @maps.route('/map/shared/<string:shareCode>')
    def showSharedSingleTrack(shareCode: str):
        track = get_track_by_share_code(shareCode)

        if track is None:
            return render_template('maps/mapNotFound.jinja2')

        return render_template(
            'maps/mapSingleTrack.jinja2',
            track=TrackModel.create_from_track(track),
            gpxUrl=url_for('gpxTracks.downloadGpxTrackBySharedTrack', shareCode=shareCode),
        )

    @maps.route('/map/plannedTour/<int:tour_id>')
    @login_required
    def showPlannedTour(tour_id: int):
        plannedTour = get_planned_tour_by_id(tour_id)

        if plannedTour is None:
            abort(404)

        return render_template(
            'maps/mapPlannedTour.jinja2',
            plannedTour=PlannedTourModel.create_from_tour(plannedTour, True),
            gpxUrl=url_for('gpxTracks.downloadGpxTrackByPlannedTourId', tour_id=tour_id),
            editUrl=url_for('plannedTours.edit', tour_id=tour_id),
        )

    @maps.route('/map/plannedTour/shared/<string:shareCode>')
    def showSharedPlannedTour(shareCode: str):
        plannedTour = get_planned_tour_by_share_code(shareCode)

        if plannedTour is None:
            return render_template('maps/mapNotFound.jinja2')

        return render_template(
            'maps/mapPlannedTour.jinja2',
            plannedTour=PlannedTourModel.create_from_tour(plannedTour, False),
            gpxUrl=url_for('gpxTracks.downloadGpxTrackBySharedPlannedTour', shareCode=shareCode),
        )

    @maps.route('/toggleYears', methods=['POST'])
    @login_required
    def toggleYears():
        activeYears = [int(item) for item in request.form.getlist('activeYears')]

        session['mapYearFilterState'] = activeYears

        return redirect(url_for('maps.showAllTracksOnMap'))

    @maps.route('/map/plannedTours')
    @login_required
    def showAllPlannedToursOnMap():
        quickFilterState = get_quick_filter_state_from_session()

        gpxInfo = []

        plannedTours: list[PlannedTour] = (
            PlannedTour.query.filter(
                or_(
                    PlannedTour.user_id == current_user.id,
                    PlannedTour.shared_users.any(id=current_user.id),
                )
            )
            .filter(PlannedTour.type.in_(quickFilterState.get_active_types()))
            .order_by(PlannedTour.name.asc())
            .all()
        )

        for tour in plannedTours:
            gpxInfo.append(createGpxInfoPlannedTour(tour.id, tour.name))  # type: ignore[arg-type]

        return render_template(
            'maps/mapMultipleTracks.jinja2',
            gpxInfo=gpxInfo,
            quickFilterState=quickFilterState,
            mapMode='plannedTours',
            redirectUrl='maps.showAllPlannedToursOnMap',
        )

    @maps.route('/map/<int:track_id>/renderTile/<int:user_id>/<int:zoom>/<int:x>/<int:y>.png')
    def renderTile(track_id: int, user_id: int, zoom: int, x: int, y: int):
        if not current_user.is_authenticated:
            abort(401)

        if current_user.id != user_id:
            abort(403)

        track = get_track_by_id(track_id)

        if track is None:
            abort(404)

        gpxMetadata = track.get_gpx_metadata()

        if gpxMetadata is None:
            visitedTiles = set()
        else:
            gpxTrackPath = os.path.join(uploadFolder, gpxMetadata.gpx_file_name)
            color = ImageColor.getcolor(track.type.tile_color, 'RGBA')
            # TODO:
            gpxMetaInfo = cachedGpxService.get_meta_info(gpxTrackPath, color)  # type: ignore[arg-type]
            visitedTiles = gpxMetaInfo.visitedTiles

        tileRenderService = TileRenderService(
            tileHuntingSettings['baseZoomLevel'], 256, visitedTiles
        )
        borderColor = ImageColor.getcolor(tileHuntingSettings['borderColor'], 'RGBA')

        image = tileRenderService.render_image(x, y, zoom, borderColor)  # type: ignore[arg-type]

        with io.BytesIO() as output:
            image.save(output, format='PNG')
            return Response(output.getvalue(), mimetype='image/png')

    @maps.route('/map/renderAllTiles/<int:user_id>/<int:zoom>/<int:x>/<int:y>.png')
    def renderAllTiles(user_id: int, zoom: int, x: int, y: int):
        if not current_user.is_authenticated:
            abort(401)

        if current_user.id != user_id:
            abort(403)

        quickFilterState = get_quick_filter_state_from_session()
        availableYears = get_available_years()
        yearFilterState = __get_map_year_filter_state_from_session(availableYears)

        visitedTiles = VisitedTileService.calculate_visited_tiles(
            quickFilterState, yearFilterState, uploadFolder, cachedGpxService
        )

        tileRenderService = TileRenderService(
            tileHuntingSettings['baseZoomLevel'], 256, visitedTiles
        )
        borderColor = ImageColor.getcolor(tileHuntingSettings['borderColor'], 'RGBA')

        image = tileRenderService.render_image(x, y, zoom, borderColor)  # type: ignore[arg-type]

        with io.BytesIO() as output:
            image.save(output, format='PNG')
            return Response(output.getvalue(), mimetype='image/png')

    @maps.route('/map/tileHunting')
    @login_required
    def showTileHuntingMap():
        quickFilterState = get_quick_filter_state_from_session()
        availableYears = get_available_years()
        yearFilterState = __get_map_year_filter_state_from_session(availableYears)

        tileRenderUrl = url_for(
            'maps.renderAllTiles',
            user_id=current_user.id,
            zoom=0,
            x=0,
            y=0,
            _external=True,
        )

        tileRenderUrl = tileRenderUrl.split('/0/0/0')[0]

        visitedTiles = VisitedTileService.calculate_visited_tiles(
            quickFilterState, yearFilterState, uploadFolder, cachedGpxService
        )

        return render_template(
            'maps/mapTileHunting.jinja2',
            quickFilterState=quickFilterState,
            yearFilterState=yearFilterState,
            availableYears=availableYears,
            redirectUrl='maps.showTileHuntingMap',
            tileRenderUrl=tileRenderUrl,
            totalNumberOfTiles=len(visitedTiles),
        )

    return maps


def __get_map_year_filter_state_from_session(availableYears: list[int]) -> list[int]:
    if 'mapYearFilterState' not in session:
        session['mapYearFilterState'] = availableYears

    return sorted(session['mapYearFilterState'])
