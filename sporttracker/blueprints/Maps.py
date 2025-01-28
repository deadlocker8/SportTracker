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
from sporttracker.blueprints.Workouts import DistanceWorkoutModel
from sporttracker.logic import Constants
from sporttracker.logic.GpxService import GpxService
from sporttracker.logic.NewVisitedTileCache import NewVisitedTileCache
from sporttracker.logic.QuickFilterState import get_quick_filter_state_from_session
from sporttracker.logic.TileRenderService import TileRenderService
from sporttracker.logic.VisitedTileService import VisitedTileService
from sporttracker.logic.model.DistanceWorkout import (
    get_available_years,
    DistanceWorkout,
    get_distance_workout_by_id,
    get_distance_workout_by_share_code,
)
from sporttracker.logic.model.PlannedTour import (
    get_planned_tour_by_id,
    PlannedTour,
    get_planned_tour_by_share_code,
)
from sporttracker.logic.model.User import get_user_by_tile_hunting_shared_code
from sporttracker.logic.model.WorkoutType import WorkoutType

LOGGER = logging.getLogger(Constants.APP_NAME)


def createGpxInfo(
    workoutId: int, workoutName: str, workoutStartTime: datetime, workoutType: WorkoutType
) -> dict[str, str | int]:
    if workoutType == WorkoutType.FITNESS:
        workoutUrl = url_for('fitnessWorkouts.edit', workout_id=workoutId)
    else:
        workoutUrl = url_for('distanceWorkouts.edit', workout_id=workoutId)

    return {
        'workoutId': workoutId,
        'gpxUrl': url_for(
            'gpxTracks.downloadGpxTrackByWorkoutId',
            workout_id=workoutId,
            file_format=GpxService.GPX_FILE_EXTENSION,
        ),
        'workoutUrl': workoutUrl,
        'workoutName': f'{workoutStartTime.strftime("%Y-%m-%d")} - {workoutName}',
    }


def createGpxInfoPlannedTour(tourId: int, tourName: str) -> dict[str, str | int]:
    return {
        'workoutId': tourId,
        'gpxUrl': url_for(
            'gpxTracks.downloadGpxTrackByPlannedTourId',
            tour_id=tourId,
            file_format=GpxService.GPX_FILE_EXTENSION,
        ),
        'workoutUrl': url_for('plannedTours.edit', tour_id=tourId),
        'workoutName': tourName,
    }


def construct_blueprint(
    tileHuntingSettings: dict[str, Any], newVisitedTileCache: NewVisitedTileCache
) -> Blueprint:
    maps = Blueprint('maps', __name__, static_folder='static')

    @maps.route('/map')
    @login_required
    def showAllWorkoutsOnMap():
        quickFilterState = get_quick_filter_state_from_session()
        availableYears = get_available_years(current_user.id)
        yearFilterState = __get_map_year_filter_state_from_session(availableYears)

        gpxInfo = []

        funcStartTime = func.max(DistanceWorkout.start_time)
        workouts = (
            DistanceWorkout.query.with_entities(
                func.max(DistanceWorkout.id),
                DistanceWorkout.name,
                funcStartTime,
                func.max(DistanceWorkout.type),
            )
            .filter(DistanceWorkout.user_id == current_user.id)
            .filter(DistanceWorkout.gpx_metadata_id.isnot(None))
            .filter(DistanceWorkout.type.in_(quickFilterState.get_active_distance_workout_types()))
            .filter(extract('year', DistanceWorkout.start_time).in_(yearFilterState))
            .group_by(DistanceWorkout.name)
            .order_by(funcStartTime.desc())
            .all()
        )

        for workout in workouts:
            workoutId, workoutName, workoutStartTime, workoutType = workout
            gpxInfo.append(createGpxInfo(workoutId, workoutName, workoutStartTime, workoutType))

        return render_template(
            'maps/mapMultipleWorkouts.jinja2',
            gpxInfo=gpxInfo,
            quickFilterState=quickFilterState,
            yearFilterState=yearFilterState,
            availableYears=availableYears,
            mapMode='workouts',
            redirectUrl='maps.showAllWorkoutsOnMap',
        )

    @maps.route('/map/<int:workout_id>')
    @login_required
    def showSingleWorkout(workout_id: int):
        workout = get_distance_workout_by_id(workout_id)

        if workout is None:
            abort(404)

        tileRenderUrl = url_for(
            'maps.renderTile',
            workout_id=workout_id,
            user_id=current_user.id,
            zoom=0,
            x=0,
            y=0,
            _external=True,
        )
        tileRenderUrl = tileRenderUrl.split('/0/0/0')[0]

        return render_template(
            'maps/mapSingleWorkout.jinja2',
            workout=DistanceWorkoutModel.create_from_workout(workout),
            gpxUrl=url_for(
                'gpxTracks.downloadGpxTrackByWorkoutId',
                workout_id=workout_id,
                file_format=GpxService.GPX_FILE_EXTENSION,
            ),
            editUrl=url_for('distanceWorkouts.edit', workout_id=workout_id),
            tileRenderUrl=tileRenderUrl,
            tileHuntingIsShowTilesActive=__get_tile_hunting_is_show_tiles_active(),
            tileHuntingIsGridActive=__get_tile_hunting_is_grid_active(),
        )

    @maps.route('/map/shared/<string:shareCode>')
    def showSharedSingleWorkout(shareCode: str):
        workout = get_distance_workout_by_share_code(shareCode)

        if workout is None:
            return render_template('maps/mapNotFound.jinja2')

        return render_template(
            'maps/mapSingleWorkout.jinja2',
            workout=DistanceWorkoutModel.create_from_workout(workout),
            gpxUrl=url_for(
                'gpxTracks.downloadGpxTrackBySharedWorkout',
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
            .filter(PlannedTour.type.in_(quickFilterState.get_active_distance_workout_types()))
            .order_by(PlannedTour.name.asc())
            .all()
        )

        for tour in plannedTours:
            gpxInfo.append(createGpxInfoPlannedTour(tour.id, tour.name))  # type: ignore[arg-type]

        return render_template(
            'maps/mapMultipleWorkouts.jinja2',
            gpxInfo=gpxInfo,
            quickFilterState=quickFilterState,
            mapMode='plannedTours',
            redirectUrl='maps.showAllPlannedToursOnMap',
        )

    @maps.route('/map/<int:workout_id>/renderTile/<int:user_id>/<int:zoom>/<int:x>/<int:y>.png')
    def renderTile(workout_id: int, user_id: int, zoom: int, x: int, y: int):
        if not current_user.is_authenticated:
            abort(401)

        if current_user.id != user_id:
            abort(403)

        workout = get_distance_workout_by_id(workout_id)

        if workout is None:
            abort(404)

        quickFilterState = get_quick_filter_state_from_session()
        availableYears = get_available_years(user_id)
        yearFilterState = __get_map_year_filter_state_from_session(availableYears)

        visitedTileService = VisitedTileService(
            newVisitedTileCache, quickFilterState, yearFilterState, workoutId=workout.id
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
        for entry in visitedTileService.get_new_tiles_per_workout():
            dates.append(flask_babel.format_date(entry.startTime, 'short'))
            values.append(entry.numberOfNewTiles)
            colors.append(entry.type.background_color_hex)
            names.append(entry.name)

        chartDataNewTilesPerWorkout = {
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
            chartDataNewTilesPerWorkout=chartDataNewTilesPerWorkout,
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
