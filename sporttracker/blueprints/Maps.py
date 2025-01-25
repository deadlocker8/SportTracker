import io
import logging
from datetime import datetime
from typing import Any

import flask_babel
from PIL import ImageColor
from flask import Blueprint, render_template, abort, url_for, session, redirect, request, Response
from flask_login import login_required, current_user
from sqlalchemy import func, extract, or_

from sporttracker.blueprints.PlannedTours import PlannedTourModel
from sporttracker.blueprints.Sports import DistanceSportModel
from sporttracker.logic import Constants
from sporttracker.logic.GpxService import GpxService
from sporttracker.logic.NewVisitedTileCache import NewVisitedTileCache
from sporttracker.logic.QuickFilterState import get_quick_filter_state_from_session
from sporttracker.logic.TileRenderService import TileRenderService
from sporttracker.logic.VisitedTileService import VisitedTileService
from sporttracker.logic.model.DistanceSport import (
    get_available_years,
    DistanceSport,
    get_distance_sport_by_id,
    get_distance_sport_by_share_code,
)
from sporttracker.logic.model.PlannedTour import (
    get_planned_tour_by_id,
    PlannedTour,
    get_planned_tour_by_share_code,
)
from sporttracker.logic.model.User import get_user_by_tile_hunting_shared_code

LOGGER = logging.getLogger(Constants.APP_NAME)


def createGpxInfo(sportId: int, trackName: str, trackStartTime: datetime) -> dict[str, str | int]:
    return {
        'trackId': sportId,
        'gpxUrl': url_for(
            'gpxTracks.downloadGpxTrackByTrackId',
            sport_id=sportId,
            file_format=GpxService.GPX_FILE_EXTENSION,
        ),
        'trackUrl': url_for('tracks.edit', sport_id=sportId),
        'trackName': f'{trackStartTime.strftime("%Y-%m-%d")} - {trackName}',
    }


def createGpxInfoPlannedTour(tourId: int, tourName: str) -> dict[str, str | int]:
    return {
        'trackId': tourId,
        'gpxUrl': url_for(
            'gpxTracks.downloadGpxTrackByPlannedTourId',
            tour_id=tourId,
            file_format=GpxService.GPX_FILE_EXTENSION,
        ),
        'trackUrl': url_for('plannedTours.edit', tour_id=tourId),
        'trackName': tourName,
    }


def construct_blueprint(
    tileHuntingSettings: dict[str, Any], newVisitedTileCache: NewVisitedTileCache
) -> Blueprint:
    maps = Blueprint('maps', __name__, static_folder='static')

    @maps.route('/map')
    @login_required
    def showAllTracksOnMap():
        quickFilterState = get_quick_filter_state_from_session()
        availableYears = get_available_years(current_user.id)
        yearFilterState = __get_map_year_filter_state_from_session(availableYears)

        gpxInfo = []

        funcStartTime = func.max(DistanceSport.start_time)
        sports = (
            DistanceSport.query.with_entities(
                func.max(DistanceSport.id), DistanceSport.name, funcStartTime
            )
            .filter(DistanceSport.user_id == current_user.id)
            .filter(DistanceSport.gpx_metadata_id.isnot(None))
            .filter(DistanceSport.type.in_(quickFilterState.get_active_distance_sport_types()))
            .filter(extract('year', DistanceSport.start_time).in_(yearFilterState))
            .group_by(DistanceSport.name)
            .order_by(funcStartTime.desc())
            .all()
        )

        for sport in sports:
            sportId, sportName, sportStartTime = sport
            gpxInfo.append(createGpxInfo(sportId, sportName, sportStartTime))

        return render_template(
            'maps/mapMultipleTracks.jinja2',
            gpxInfo=gpxInfo,
            quickFilterState=quickFilterState,
            yearFilterState=yearFilterState,
            availableYears=availableYears,
            mapMode='tracks',
            redirectUrl='maps.showAllTracksOnMap',
        )

    @maps.route('/map/<int:sport_id>')
    @login_required
    def showSingleTrack(sport_id: int):
        sport = get_distance_sport_by_id(sport_id)

        if sport is None:
            abort(404)

        tileRenderUrl = url_for(
            'maps.renderTile',
            sport_id=sport_id,
            user_id=current_user.id,
            zoom=0,
            x=0,
            y=0,
            _external=True,
        )
        tileRenderUrl = tileRenderUrl.split('/0/0/0')[0]

        return render_template(
            'maps/mapSingleTrack.jinja2',
            sport=DistanceSportModel.create_from_sport(sport),
            gpxUrl=url_for(
                'gpxTracks.downloadGpxTrackByTrackId',
                sport_id=sport_id,
                file_format=GpxService.GPX_FILE_EXTENSION,
            ),
            editUrl=url_for('distanceSports.edit', sport_id=sport_id),
            tileRenderUrl=tileRenderUrl,
            tileHuntingIsShowTilesActive=__get_tile_hunting_is_show_tiles_active(),
            tileHuntingIsGridActive=__get_tile_hunting_is_grid_active(),
        )

    @maps.route('/map/shared/<string:shareCode>')
    def showSharedSingleTrack(shareCode: str):
        sport = get_distance_sport_by_share_code(shareCode)

        if sport is None:
            return render_template('maps/mapNotFound.jinja2')

        return render_template(
            'maps/mapSingleTrack.jinja2',
            sport=DistanceSportModel.create_from_sport(sport),
            gpxUrl=url_for(
                'gpxTracks.downloadGpxTrackBySharedTrack',
                shareCode=shareCode,
                file_format=GpxService.GPX_FILE_EXTENSION,
            ),
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
            gpxUrl=url_for(
                'gpxTracks.downloadGpxTrackByPlannedTourId',
                tour_id=tour_id,
                file_format=GpxService.GPX_FILE_EXTENSION,
            ),
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
            gpxUrl=url_for(
                'gpxTracks.downloadGpxTrackBySharedPlannedTour',
                shareCode=shareCode,
                file_format='gpx',
            ),
        )

    @maps.route('/toggleYears', methods=['POST'])
    @login_required
    def toggleYears():
        activeYears = [int(item) for item in request.form.getlist('activeYears')]
        redirectUrl = request.form['redirectUrl']

        session['mapYearFilterState'] = activeYears

        return redirect(redirectUrl)

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
            .filter(PlannedTour.type.in_(quickFilterState.get_active_distance_sport_types()))
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

    @maps.route('/map/<int:sport_id>/renderTile/<int:user_id>/<int:zoom>/<int:x>/<int:y>.png')
    def renderTile(sport_id: int, user_id: int, zoom: int, x: int, y: int):
        if not current_user.is_authenticated:
            abort(401)

        if current_user.id != user_id:
            abort(403)

        sport = get_distance_sport_by_id(sport_id)

        if sport is None:
            abort(404)

        quickFilterState = get_quick_filter_state_from_session()
        availableYears = get_available_years(user_id)
        yearFilterState = __get_map_year_filter_state_from_session(availableYears)

        visitedTileService = VisitedTileService(
            newVisitedTileCache, quickFilterState, yearFilterState, sportId=sport.id
        )

        tileRenderService = TileRenderService(
            tileHuntingSettings['baseZoomLevel'], 256, visitedTileService
        )

        borderColor = None
        if __get_tile_hunting_is_grid_active():
            borderColor = ImageColor.getcolor(tileHuntingSettings['borderColor'], 'RGBA')

        image = tileRenderService.render_image(x, y, zoom, user_id, borderColor)  # type: ignore[arg-type]

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
        availableYears = get_available_years(user_id)
        yearFilterState = __get_map_year_filter_state_from_session(availableYears)

        visitedTileService = VisitedTileService(
            newVisitedTileCache, quickFilterState, yearFilterState
        )
        tileRenderService = TileRenderService(
            tileHuntingSettings['baseZoomLevel'], 256, visitedTileService
        )

        borderColor = None
        if __get_tile_hunting_is_grid_active():
            borderColor = ImageColor.getcolor(tileHuntingSettings['borderColor'], 'RGBA')

        image = tileRenderService.render_image(x, y, zoom, user_id, borderColor)  # type: ignore[arg-type]

        with io.BytesIO() as output:
            image.save(output, format='PNG')
            return Response(output.getvalue(), mimetype='image/png')

    @maps.route('/map/tileOverlay/<string:share_code>/<int:zoom>/<int:x>/<int:y>.png')
    def renderAllTilesViaShareCode(share_code: str, zoom: int, x: int, y: int):
        user = get_user_by_tile_hunting_shared_code(share_code)
        if user is None:
            abort(404)

        quickFilterState = get_quick_filter_state_from_session()
        availableYears = get_available_years(user.id)
        yearFilterState = __get_map_year_filter_state_from_session(availableYears)

        visitedTileService = VisitedTileService(
            newVisitedTileCache, quickFilterState, yearFilterState
        )
        tileRenderService = TileRenderService(
            tileHuntingSettings['baseZoomLevel'], 256, visitedTileService
        )

        borderColor = ImageColor.getcolor(tileHuntingSettings['borderColor'], 'RGBA')
        image = tileRenderService.render_image(x, y, zoom, user.id, borderColor)  # type: ignore[arg-type]

        with io.BytesIO() as output:
            image.save(output, format='PNG')
            return Response(output.getvalue(), mimetype='image/png')

    @maps.route('/map/tileHunting')
    @login_required
    def showTileHuntingMap():
        tileRenderUrl = url_for(
            'maps.renderAllTiles',
            user_id=current_user.id,
            zoom=0,
            x=0,
            y=0,
            _external=True,
        )

        tileRenderUrl = tileRenderUrl.split('/0/0/0')[0]

        quickFilterState = get_quick_filter_state_from_session()
        availableYears = get_available_years(current_user.id)
        yearFilterState = __get_map_year_filter_state_from_session(availableYears)

        visitedTileService = VisitedTileService(
            newVisitedTileCache, quickFilterState, yearFilterState
        )
        totalNumberOfTiles = visitedTileService.calculate_total_number_of_visited_tiles()

        dates = []
        values = []
        colors = []
        names = []
        for entry in visitedTileService.get_new_tiles_per_track():
            dates.append(flask_babel.format_date(entry.startTime, 'short'))
            values.append(entry.numberOfNewTiles)
            colors.append(entry.type.background_color_hex)
            names.append(entry.name)

        chartDataNewTilesPerTrack = {
            'dates': dates,
            'values': values,
            'colors': colors,
            'names': names,
        }

        return render_template(
            'maps/mapTileHunting.jinja2',
            quickFilterState=quickFilterState,
            yearFilterState=yearFilterState,
            availableYears=availableYears,
            redirectUrl='maps.showTileHuntingMap',
            tileRenderUrl=tileRenderUrl,
            totalNumberOfTiles=totalNumberOfTiles,
            chartDataNewTilesPerTrack=chartDataNewTilesPerTrack,
            tileHuntingIsGridActive=__get_tile_hunting_is_grid_active(),
        )

    @maps.route('/toggleTileHuntingViewTiles')
    @login_required
    def toggleTileHuntingViewTiles():
        redirectUrl = request.args['redirectUrl']
        session['tileHuntingIsShowTilesActive'] = not __get_tile_hunting_is_show_tiles_active()
        return redirect(redirectUrl)

    @maps.route('/toggleTileHuntingViewGrid')
    @login_required
    def toggleTileHuntingViewGrid():
        redirectUrl = request.args['redirectUrl']
        session['tileHuntingIsGridActive'] = not __get_tile_hunting_is_grid_active()
        return redirect(redirectUrl)

    return maps


def __get_map_year_filter_state_from_session(availableYears: list[int]) -> list[int]:
    if 'mapYearFilterState' not in session:
        session['mapYearFilterState'] = availableYears

    return sorted(session['mapYearFilterState'])


def __get_tile_hunting_is_show_tiles_active() -> bool:
    if 'tileHuntingIsShowTilesActive' not in session:
        session['tileHuntingIsShowTilesActive'] = True

    return session['tileHuntingIsShowTilesActive']


def __get_tile_hunting_is_grid_active() -> bool:
    if 'tileHuntingIsGridActive' not in session:
        session['tileHuntingIsGridActive'] = False

    return session['tileHuntingIsGridActive']
