import io
import logging
from datetime import datetime
from operator import attrgetter
from typing import Any

import flask_babel
from PIL import ImageColor
from flask import (
    Blueprint,
    render_template,
    abort,
    url_for,
    session,
    redirect,
    request,
    Response,
    jsonify,
)
from flask_login import login_required, current_user
from natsort import natsorted, natsort
from sqlalchemy import func, extract, or_

from sporttracker.blueprints.LongDistanceTours import LongDistanceTourModel
from sporttracker.blueprints.PlannedTours import PlannedTourModel
from sporttracker.blueprints.Workouts import DistanceWorkoutModel
from sporttracker.logic import Constants
from sporttracker.logic.GpxService import GpxService, GpxParser
from sporttracker.logic.QuickFilterState import (
    get_quick_filter_state_from_session,
    QuickFilterState,
)
from sporttracker.logic.model.DistanceWorkout import (
    get_available_years,
    DistanceWorkout,
)
from sporttracker.logic.model.LongDistanceTour import get_long_distance_tour_by_id
from sporttracker.logic.model.PlannedTour import PlannedTour
from sporttracker.logic.model.User import get_user_by_tile_hunting_shared_code
from sporttracker.logic.model.WorkoutType import WorkoutType
from sporttracker.logic.service.DistanceWorkoutService import DistanceWorkoutService
from sporttracker.logic.service.PlannedTourService import PlannedTourService
from sporttracker.logic.tileHunting.MaxSquareCache import MaxSquareCache
from sporttracker.logic.tileHunting.NewVisitedTileCache import NewVisitedTileCache
from sporttracker.logic.tileHunting.TileRenderService import TileRenderService, TileRenderColorMode
from sporttracker.logic.tileHunting.VisitedTileService import VisitedTileService

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
        'workoutName': f'{workoutStartTime.strftime("%Y-%m-%d")} - {__escape_name(workoutName)}',
    }


def createGpxInfoPlannedTour(tourId: int, tourName: str, workoutUrlEndpoint: str) -> dict[str, str | int]:
    return {
        'workoutId': tourId,
        'gpxUrl': url_for(
            'gpxTracks.downloadGpxTrackByPlannedTourId',
            tour_id=tourId,
            file_format=GpxService.GPX_FILE_EXTENSION,
        ),
        'workoutUrl': workoutUrlEndpoint,
        'workoutName': __escape_name(tourName),
    }


def construct_blueprint(
    tileHuntingSettings: dict[str, Any],
    newVisitedTileCache: NewVisitedTileCache,
    maxSquareCache: MaxSquareCache,
    distanceWorkoutService: DistanceWorkoutService,
    gpxPreviewImageSettings: dict[str, Any],
    plannedTourService: PlannedTourService,
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
        workout = distanceWorkoutService.get_distance_workout_by_id(workout_id, current_user.id)

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

        tileHuntingNumberOfNewVisitedTiles = 0

        quickFilterState = QuickFilterState()
        quickFilterState.disable_all()
        quickFilterState.toggle_state(workout.type)

        visitedTileService = __create_visited_tile_service(quickFilterState, get_available_years(current_user.id))
        newVisitedTilesPerWorkout = visitedTileService.get_number_of_new_tiles_per_workout()
        filtered = [x for x in newVisitedTilesPerWorkout if x.distance_workout_id == workout_id]
        if filtered:
            tileHuntingNumberOfNewVisitedTiles = filtered[0].numberOfNewTiles

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
            tileHuntingIsOnlyHighlightNewTilesActive=__get_tile_hunting_is_only_highlight_new_tiles(),
            tileHuntingNumberOfNewVisitedTiles=tileHuntingNumberOfNewVisitedTiles,
        )

    @maps.route('/map/shared/<string:shareCode>')
    def showSharedSingleWorkout(shareCode: str):
        workout = distanceWorkoutService.get_distance_workout_by_share_code(shareCode)

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
        plannedTour = PlannedTourService.get_planned_tour_by_id(tour_id)

        if plannedTour is None:
            abort(404)

        tileRenderUrl = url_for(
            'maps.renderAllTiles',
            user_id=current_user.id,
            zoom=0,
            x=0,
            y=0,
            _external=True,
        )

        tileRenderUrl = tileRenderUrl.split('/0/0/0')[0]

        return render_template(
            'maps/mapPlannedTour.jinja2',
            plannedTour=PlannedTourModel.create_from_tour(plannedTour, True),
            gpxUrl=url_for(
                'gpxTracks.downloadGpxTrackByPlannedTourId',
                tour_id=tour_id,
                file_format=GpxService.GPX_FILE_EXTENSION,
            ),
            editUrl=url_for('plannedTours.edit', tour_id=tour_id),
            tileRenderUrl=tileRenderUrl,
            tileHuntingIsShowTilesActive=__get_tile_hunting_is_show_tiles_active(),
            tileHuntingIsGridActive=__get_tile_hunting_is_grid_active(),
            tileHuntingIsMaxSquareActive=__get_tile_hunting_is_max_square_active(),
            tileHuntingNumberOfNewVisitedTiles=plannedTourService.get_number_of_new_visited_tiles(plannedTour),
        )

    @maps.route('/map/plannedTour/shared/<string:shareCode>')
    def showSharedPlannedTour(shareCode: str):
        plannedTour = PlannedTourService.get_planned_tour_by_share_code(shareCode)

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
            .all()
        )
        plannedTours = natsorted(plannedTours, alg=natsort.ns.IGNORECASE, key=attrgetter('name'))

        for tour in plannedTours:
            gpxInfo.append(createGpxInfoPlannedTour(tour.id, tour.name, url_for('plannedTours.edit', tour_id=tour.id)))  # type: ignore[arg-type]

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

        workout = distanceWorkoutService.get_distance_workout_by_id(workout_id, current_user.id)

        if workout is None:
            abort(404)

        quickFilterState = get_quick_filter_state_from_session()
        availableYears = get_available_years(user_id)
        yearFilterState = __get_map_year_filter_state_from_session(availableYears)

        visitedTileService = VisitedTileService(
            newVisitedTileCache,
            maxSquareCache,
            quickFilterState,
            yearFilterState,
            distanceWorkoutService,
            workoutId=workout.id,
            onlyHighlightNewTiles=__get_tile_hunting_is_only_highlight_new_tiles(),
        )

        tileRenderService = TileRenderService(tileHuntingSettings['baseZoomLevel'], 256, visitedTileService)

        borderColor = None
        if __get_tile_hunting_is_grid_active():
            borderColor = ImageColor.getcolor(tileHuntingSettings['borderColor'], 'RGBA')

        image = tileRenderService.render_image(
            x,
            y,
            zoom,
            user_id,
            TileRenderColorMode.NUMBER_OF_WORKOUT_TYPES,
            borderColor,  # type: ignore[arg-type]
            None,
        )

        with io.BytesIO() as output:
            image.save(output, format='PNG')
            return Response(output.getvalue(), mimetype='image/png')

    @maps.route('/map/renderAllTiles/<int:user_id>/<int:zoom>/<int:x>/<int:y>.png')
    def renderAllTiles(user_id: int, zoom: int, x: int, y: int):
        if not current_user.is_authenticated:
            abort(401)

        if current_user.id != user_id:
            abort(403)

        return __renderTile(user_id, zoom, x, y, QuickFilterState(), get_available_years(user_id))

    @maps.route('/map/renderAllTilesWithFilter/<int:user_id>/<int:zoom>/<int:x>/<int:y>.png')
    def renderAllTilesWithFilter(user_id: int, zoom: int, x: int, y: int):
        if not current_user.is_authenticated:
            abort(401)

        if current_user.id != user_id:
            abort(403)

        quickFilterState = get_quick_filter_state_from_session()
        availableYears = get_available_years(user_id)
        yearFilterState = __get_map_year_filter_state_from_session(availableYears)

        return __renderTile(user_id, zoom, x, y, quickFilterState, yearFilterState)

    def __renderTile(
        user_id: int, zoom: int, x: int, y: int, quickFilterState: QuickFilterState, yearFilterState: list[int]
    ) -> Response:
        visitedTileService = __create_visited_tile_service(quickFilterState, yearFilterState)
        tileRenderService = TileRenderService(tileHuntingSettings['baseZoomLevel'], 256, visitedTileService)

        borderColor = None
        if __get_tile_hunting_is_grid_active():
            borderColor = ImageColor.getcolor(tileHuntingSettings['borderColor'], 'RGBA')

        maxSquareColor = None
        if __get_tile_hunting_is_max_square_active():
            maxSquareColor = ImageColor.getcolor(tileHuntingSettings['maxSquareColor'], 'RGBA')

        image = tileRenderService.render_image(
            x,
            y,
            zoom,
            user_id,
            TileRenderColorMode.NUMBER_OF_WORKOUT_TYPES,
            borderColor,  # type: ignore[arg-type]
            maxSquareColor,  # type: ignore[arg-type]
        )

        with io.BytesIO() as output:
            image.save(output, format='PNG')
            return Response(output.getvalue(), mimetype='image/png')

    @maps.route('/map/renderHeatmap/<int:user_id>/<int:zoom>/<int:x>/<int:y>.png')
    def renderHeatmap(user_id: int, zoom: int, x: int, y: int):
        if not current_user.is_authenticated:
            abort(401)

        if current_user.id != user_id:
            abort(403)

        availableYears = get_available_years(user_id)
        yearFilterState = __get_map_year_filter_state_from_session(availableYears)

        visitedTileService = __create_visited_tile_service(QuickFilterState(), yearFilterState)
        tileRenderService = TileRenderService(tileHuntingSettings['baseZoomLevel'], 256, visitedTileService)

        borderColor = None
        if __get_tile_hunting_is_grid_active():
            borderColor = ImageColor.getcolor(tileHuntingSettings['borderColor'], 'RGBA')

        image = tileRenderService.render_image(
            x,
            y,
            zoom,
            user_id,
            TileRenderColorMode.NUMBER_OF_VISITS,
            borderColor,  # type: ignore[arg-type]
            None,
        )

        with io.BytesIO() as output:
            image.save(output, format='PNG')
            return Response(output.getvalue(), mimetype='image/png')

    @maps.route('/map/tileOverlay/<string:share_code>/<int:zoom>/<int:x>/<int:y>.png')
    def renderAllTileHuntingTilesViaShareCode(share_code: str, zoom: int, x: int, y: int):
        user = get_user_by_tile_hunting_shared_code(share_code)
        if user is None:
            abort(404)

        visitedTileService = __create_visited_tile_service(QuickFilterState(), get_available_years(user.id))
        tileRenderService = TileRenderService(tileHuntingSettings['baseZoomLevel'], 256, visitedTileService)

        borderColor = ImageColor.getcolor(tileHuntingSettings['borderColor'], 'RGBA')
        image = tileRenderService.render_image(
            x,
            y,
            zoom,
            user.id,
            TileRenderColorMode.NUMBER_OF_WORKOUT_TYPES,
            borderColor,  # type: ignore[arg-type]
            None,
        )

        with io.BytesIO() as output:
            image.save(output, format='PNG')
            return Response(output.getvalue(), mimetype='image/png')

    @maps.route('/map/tileHunting')
    @login_required
    def showTileHuntingMap():
        tileRenderUrl = url_for(
            'maps.renderAllTilesWithFilter',
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

        visitedTileService = __create_visited_tile_service(quickFilterState, yearFilterState)
        totalNumberOfTiles = visitedTileService.calculate_total_number_of_visited_tiles()

        dates = []
        values = []
        colors = []
        customData = []
        for entry in visitedTileService.get_number_of_new_tiles_per_workout():
            dates.append(flask_babel.format_date(entry.startTime, 'short'))
            values.append(entry.numberOfNewTiles)
            colors.append(entry.type.background_color_hex)

            customData.append(
                {
                    'name': entry.name,
                    'url': url_for('maps.showSingleWorkout', workout_id=entry.distance_workout_id),
                }
            )

        chartDataNewTilesPerWorkout = {
            'dates': dates,
            'values': values,
            'colors': colors,
            'names': customData,
        }

        return render_template(
            'maps/mapTileHunting.jinja2',
            quickFilterState=quickFilterState,
            yearFilterState=yearFilterState,
            availableYears=availableYears,
            redirectUrl='maps.showTileHuntingMap',
            tileRenderUrl=tileRenderUrl,
            totalNumberOfTiles=totalNumberOfTiles,
            maxSquareSize=visitedTileService.get_max_square_size(),
            chartDataNewTilesPerWorkout=chartDataNewTilesPerWorkout,
            tileHuntingIsGridActive=__get_tile_hunting_is_grid_active(),
            tileHuntingIsMaxSquareActive=__get_tile_hunting_is_max_square_active(),
            maxSquareColor=tileHuntingSettings['maxSquareColor'],
        )

    @maps.route('/map/tileHuntingHeatmap')
    @login_required
    def showTileHuntingHeatMap():
        tileRenderUrl = url_for(
            'maps.renderHeatmap',
            user_id=current_user.id,
            zoom=0,
            x=0,
            y=0,
            _external=True,
        )
        tileRenderUrl = tileRenderUrl.split('/0/0/0')[0]

        numberOfVisitsUrl = url_for(
            'maps.getNumberOfVisitsByCoordinate',
            user_id=current_user.id,
            latitude=0,
            longitude=0,
            zoom=0,
        )
        numberOfVisitsUrl = numberOfVisitsUrl.split('/0.0/0.0')[0]

        availableYears = get_available_years(current_user.id)
        yearFilterState = __get_map_year_filter_state_from_session(availableYears)

        return render_template(
            'maps/mapTileHuntingHeatmap.jinja2',
            yearFilterState=yearFilterState,
            availableYears=availableYears,
            redirectUrl='maps.showTileHuntingHeatMap',
            tileRenderUrl=tileRenderUrl,
            numberOfVisitsUrl=numberOfVisitsUrl,
            tileHuntingIsGridActive=__get_tile_hunting_is_grid_active(),
        )

    @maps.route('/map/getNumberOfVisitsByCoordinate/<int:user_id>/<float:latitude>/<float:longitude>')
    @login_required
    def getNumberOfVisitsByCoordinate(user_id: int, latitude: float, longitude: float):
        if not current_user.is_authenticated:
            abort(401)

        if current_user.id != user_id:
            abort(403)

        visitedTile = GpxParser.convert_coordinate_to_tile_position(
            latitude, longitude, tileHuntingSettings['baseZoomLevel']
        )

        availableYears = get_available_years(user_id)
        yearFilterState = __get_map_year_filter_state_from_session(availableYears)

        visitedTileService = __create_visited_tile_service(QuickFilterState(), yearFilterState)
        rows = visitedTileService.determine_number_of_visits(
            visitedTile.x, visitedTile.x, visitedTile.y, visitedTile.y, user_id
        )
        numberOfVisits = 0
        if rows:
            numberOfVisits = rows[0].count

        return jsonify({'numberOfVisits': numberOfVisits})

    @maps.route('/map/longDistanceTour/<int:tour_id>')
    @login_required
    def showLongDistanceTour(tour_id: int):
        longDistanceTour = get_long_distance_tour_by_id(tour_id)

        if longDistanceTour is None:
            abort(404)

        tileRenderUrl = url_for(
            'maps.renderAllTiles',
            user_id=current_user.id,
            zoom=0,
            x=0,
            y=0,
            _external=True,
        )

        longDistanceTourModel = LongDistanceTourModel.create_from_tour(longDistanceTour)

        tileRenderUrl = tileRenderUrl.split('/0/0/0')[0]

        gpxInfo = []
        for order, tour in enumerate(longDistanceTourModel.linkedPlannedTours):
            tourName = f'{flask_babel.gettext("Stage")} {order + 1} - {tour.name}'
            gpxInfo.append(
                createGpxInfoPlannedTour(tour.id, tourName, url_for('maps.showPlannedTour', tour_id=tour.id))
            )  # type: ignore[arg-type]

        return render_template(
            'maps/mapLongDistanceTour.jinja2',
            longDistanceTour=longDistanceTourModel,
            gpxInfo=gpxInfo,
            editUrl=url_for('longDistanceTours.edit', tour_id=tour_id),
            tileRenderUrl=tileRenderUrl,
            tileHuntingIsShowTilesActive=__get_tile_hunting_is_show_tiles_active(),
            tileHuntingIsGridActive=__get_tile_hunting_is_grid_active(),
            tileHuntingIsMaxSquareActive=__get_tile_hunting_is_max_square_active(),
            isGpxPreviewImagesEnabled=gpxPreviewImageSettings['enabled'],
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

    @maps.route('/toggleTileHuntingOnlyHighlightNewTiles')
    @login_required
    def toggleTileHuntingOnlyHighlightNewTiles():
        redirectUrl = request.args['redirectUrl']
        session['tileHuntingIsOnlyHighlightNewTilesActive'] = not __get_tile_hunting_is_only_highlight_new_tiles()
        return redirect(redirectUrl)

    @maps.route('/toggleTileHuntingMaxSquare')
    @login_required
    def toggleTileHuntingMaxSquare():
        redirectUrl = request.args['redirectUrl']
        session['tileHuntingIsMaxSquareActive'] = not __get_tile_hunting_is_max_square_active()
        return redirect(redirectUrl)

    def __create_visited_tile_service(quickFilterState, yearFilterState):
        return VisitedTileService(
            newVisitedTileCache,
            maxSquareCache,
            quickFilterState,
            yearFilterState,
            distanceWorkoutService,
        )

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


def __get_tile_hunting_is_only_highlight_new_tiles() -> bool:
    if 'tileHuntingIsOnlyHighlightNewTilesActive' not in session:
        session['tileHuntingIsOnlyHighlightNewTilesActive'] = False

    return session['tileHuntingIsOnlyHighlightNewTilesActive']


def __get_tile_hunting_is_max_square_active() -> bool:
    if 'tileHuntingIsMaxSquareActive' not in session:
        session['tileHuntingIsMaxSquareActive'] = False

    return session['tileHuntingIsMaxSquareActive']


def __escape_name(name: str) -> str:
    return name.replace('<', '&lt;').replace('>', '&gt;')
