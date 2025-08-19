import io
import logging
from datetime import datetime
from typing import Any

import flask_babel
from PIL import ImageColor
from flask import (
    Blueprint,
    render_template,
    abort,
    url_for,
    redirect,
    request,
    Response,
    jsonify,
)
from flask_login import login_required, current_user
from sqlalchemy import func, extract

from sporttracker.longDistanceTour.LongDistanceTourBlueprint import LongDistanceTourModel
from sporttracker.plannedTour.PlannedTourBlueprint import PlannedTourModel
from sporttracker.tileHunting.MaxSquareCache import MaxSquareCache
from sporttracker.tileHunting.NewVisitedTileCache import NewVisitedTileCache
from sporttracker.tileHunting.TileRenderService import TileRenderService, TileRenderColorMode
from sporttracker.tileHunting.VisitedTileService import VisitedTileService
from sporttracker.workout.WorkoutBlueprint import DistanceWorkoutModel
from sporttracker.logic import Constants
from sporttracker.gpx.GpxService import GpxService, GpxParser
from sporttracker.workout.distance.DistanceWorkoutEntity import (
    get_available_years,
    DistanceWorkout,
)
from sporttracker.user.UserEntity import get_user_by_tile_hunting_shared_code
from sporttracker.workout.WorkoutType import WorkoutType
from sporttracker.logic.model.db import db
from sporttracker.plannedTour.PlannedTourFilterStateEntity import get_planned_tour_filter_state_by_user
from sporttracker.quickFilter.QuickFilterStateEntity import get_quick_filter_state_by_user, QuickFilterState
from sporttracker.tileHunting.TileHuntingFilterStateEntity import (
    get_tile_hunting_filter_state_by_user,
    TileHuntingFilterState,
)
from sporttracker.workout.distance.DistanceWorkoutService import DistanceWorkoutService
from sporttracker.longDistanceTour.LongDistanceTourService import LongDistanceTourService
from sporttracker.plannedTour.PlannedTourService import PlannedTourService

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
        quickFilterState = get_quick_filter_state_by_user(current_user.id)

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
            .filter(extract('year', DistanceWorkout.start_time).in_(quickFilterState.years))
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
            availableYears=get_available_years(current_user.id),
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

        quickFilterState = QuickFilterState().reset(get_available_years(current_user.id))

        tileHuntingFilterState = get_tile_hunting_filter_state_by_user(current_user.id)
        visitedTileService = __create_visited_tile_service(quickFilterState, tileHuntingFilterState)
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
            tileHuntingFilterState=get_tile_hunting_filter_state_by_user(current_user.id),
            tileHuntingNumberOfNewVisitedTiles=tileHuntingNumberOfNewVisitedTiles,
        )

    @maps.route('/map/shared/<string:shareCode>')
    def showSharedSingleWorkout(shareCode: str):
        workout = distanceWorkoutService.get_distance_workout_by_share_code(shareCode)

        if workout is None:
            return render_template('maps/mapNotFound.jinja2', errorText=flask_babel.gettext('Unknown shared link'))

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
        plannedTour = plannedTourService.get_planned_tour_by_id(tour_id)

        if plannedTour is None:
            return render_template('maps/mapNotFound.jinja2', errorText=flask_babel.gettext('Unknown planned tour'))

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
            tileHuntingFilterState=get_tile_hunting_filter_state_by_user(current_user.id),
            tileHuntingNumberOfNewVisitedTiles=plannedTourService.get_number_of_new_visited_tiles(plannedTour),
            maxSquareColor=tileHuntingSettings['maxSquareColor'],
            plannedTileColor=TileRenderService.COLOR_PLANNED,
        )

    @maps.route('/map/plannedTour/shared/<string:shareCode>')
    def showSharedPlannedTour(shareCode: str):
        plannedTour = PlannedTourService.get_planned_tour_by_share_code(shareCode)

        if plannedTour is None:
            return render_template('maps/mapNotFound.jinja2', errorText=flask_babel.gettext('Unknown shared link'))

        return render_template(
            'maps/mapPlannedTour.jinja2',
            plannedTour=PlannedTourModel.create_from_tour(plannedTour, False),
            gpxUrl=url_for(
                'gpxTracks.downloadGpxTrackBySharedPlannedTour',
                shareCode=shareCode,
                file_format='gpx',
            ),
        )

    @maps.route('/map/plannedTours')
    @login_required
    def showAllPlannedToursOnMap():
        tileRenderUrl = url_for(
            'maps.renderAllTilesWithFilter',
            user_id=current_user.id,
            zoom=0,
            x=0,
            y=0,
            _external=True,
        )

        tileRenderUrl = tileRenderUrl.split('/0/0/0')[0]

        gpxInfo = []

        quickFilterState = get_quick_filter_state_by_user(current_user.id)
        plannedTourFilterState = get_planned_tour_filter_state_by_user(current_user.id)

        plannedTours = plannedTourService.get_planned_tours_filtered(
            quickFilterState.get_active_distance_workout_types(), plannedTourFilterState
        )

        for tour in plannedTours:
            gpxInfo.append(
                createGpxInfoPlannedTour(
                    tour.id,
                    tour.name,  # type: ignore[arg-type]
                    url_for('maps.showPlannedTour', tour_id=tour.id),
                )
            )

        return render_template(
            'maps/mapMultipleWorkouts.jinja2',
            gpxInfo=gpxInfo,
            quickFilterState=quickFilterState,
            mapMode='plannedTours',
            redirectUrl='maps.showAllPlannedToursOnMap',
            tileHuntingFilterState=get_tile_hunting_filter_state_by_user(current_user.id),
            tileRenderUrl=tileRenderUrl,
            plannedTourFilterState=plannedTourFilterState,
            maxSquareColor=tileHuntingSettings['maxSquareColor'],
            plannedTileColor=TileRenderService.COLOR_PLANNED,
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

        quickFilterState = get_quick_filter_state_by_user(current_user.id)
        tileHuntingFilterState = get_tile_hunting_filter_state_by_user(current_user.id)

        visitedTileService = VisitedTileService(
            newVisitedTileCache,
            maxSquareCache,
            quickFilterState,
            tileHuntingFilterState,
            distanceWorkoutService,
            workoutId=workout.id,
        )

        tileRenderService = TileRenderService(tileHuntingSettings['baseZoomLevel'], 256, visitedTileService)

        borderColor = None
        if tileHuntingFilterState.is_show_grid_active:
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

        return __renderTile(user_id, zoom, x, y, QuickFilterState().reset(get_available_years(user_id)))

    @maps.route('/map/renderAllTilesWithFilter/<int:user_id>/<int:zoom>/<int:x>/<int:y>.png')
    def renderAllTilesWithFilter(user_id: int, zoom: int, x: int, y: int):
        if not current_user.is_authenticated:
            abort(401)

        if current_user.id != user_id:
            abort(403)

        quickFilterState = get_quick_filter_state_by_user(current_user.id)

        return __renderTile(user_id, zoom, x, y, quickFilterState)

    def __renderTile(user_id: int, zoom: int, x: int, y: int, quickFilterState: QuickFilterState) -> Response:
        tileHuntingFilterState = get_tile_hunting_filter_state_by_user(current_user.id)
        visitedTileService = __create_visited_tile_service(quickFilterState, tileHuntingFilterState)
        tileRenderService = TileRenderService(tileHuntingSettings['baseZoomLevel'], 256, visitedTileService)

        borderColor = None
        if tileHuntingFilterState.is_show_grid_active:
            borderColor = ImageColor.getcolor(tileHuntingSettings['borderColor'], 'RGBA')

        maxSquareColor = None
        if tileHuntingFilterState.is_show_max_square_active:
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

        tileHuntingFilterState = get_tile_hunting_filter_state_by_user(current_user.id)
        visitedTileService = __create_visited_tile_service(
            QuickFilterState().reset(availableYears), tileHuntingFilterState
        )
        tileRenderService = TileRenderService(tileHuntingSettings['baseZoomLevel'], 256, visitedTileService)

        borderColor = None
        if tileHuntingFilterState.is_show_grid_active:
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

        tileHuntingFilterState = TileHuntingFilterState().reset()
        tileHuntingFilterState.is_show_max_square_active = False  # type: ignore[assignment]
        tileHuntingFilterState.is_show_planned_tiles_active = user.isTileHuntingShowPlannedTilesActivated  # type: ignore[assignment]

        visitedTileService = __create_visited_tile_service(
            QuickFilterState().reset(get_available_years(user.id)), tileHuntingFilterState
        )
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

        quickFilterState = get_quick_filter_state_by_user(current_user.id)

        tileHuntingFilterState = get_tile_hunting_filter_state_by_user(current_user.id)
        visitedTileService = __create_visited_tile_service(quickFilterState, tileHuntingFilterState)
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
            availableYears=get_available_years(current_user.id),
            redirectUrl='maps.showTileHuntingMap',
            tileRenderUrl=tileRenderUrl,
            totalNumberOfTiles=totalNumberOfTiles,
            maxSquareSize=visitedTileService.get_max_square_size(),
            chartDataNewTilesPerWorkout=chartDataNewTilesPerWorkout,
            tileHuntingFilterState=get_tile_hunting_filter_state_by_user(current_user.id),
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
        quickFilterState = get_quick_filter_state_by_user(current_user.id)

        return render_template(
            'maps/mapTileHuntingHeatmap.jinja2',
            quickFilterState=quickFilterState,
            availableYears=availableYears,
            redirectUrl='maps.showTileHuntingHeatMap',
            tileRenderUrl=tileRenderUrl,
            numberOfVisitsUrl=numberOfVisitsUrl,
            tileHuntingFilterState=get_tile_hunting_filter_state_by_user(current_user.id),
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

        tileHuntingFilterState = get_tile_hunting_filter_state_by_user(current_user.id)
        visitedTileService = __create_visited_tile_service(
            QuickFilterState().reset(availableYears), tileHuntingFilterState
        )
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
        longDistanceTour = LongDistanceTourService.get_long_distance_tour_by_id(tour_id)

        if longDistanceTour is None:
            return render_template(
                'maps/mapNotFound.jinja2', errorText=flask_babel.gettext('Unknown long-distance tour')
            )

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
            tileHuntingFilterState=get_tile_hunting_filter_state_by_user(current_user.id),
            isGpxPreviewImagesEnabled=gpxPreviewImageSettings['enabled'],
            maxSquareColor=tileHuntingSettings['maxSquareColor'],
        )

    @maps.route('/toggleTileHuntingViewTiles')
    @login_required
    def toggleTileHuntingViewTiles():
        redirectUrl = request.args['redirectUrl']
        tileHuntingFilterState = get_tile_hunting_filter_state_by_user(current_user.id)
        currentValue = tileHuntingFilterState.is_show_tiles_active
        tileHuntingFilterState.is_show_tiles_active = not currentValue  # type: ignore[assignment]
        db.session.commit()

        return redirect(redirectUrl)

    @maps.route('/toggleTileHuntingViewGrid')
    @login_required
    def toggleTileHuntingViewGrid():
        redirectUrl = request.args['redirectUrl']
        tileHuntingFilterState = get_tile_hunting_filter_state_by_user(current_user.id)
        currentValue = tileHuntingFilterState.is_show_grid_active
        tileHuntingFilterState.is_show_grid_active = not currentValue  # type: ignore[assignment]
        db.session.commit()

        return redirect(redirectUrl)

    @maps.route('/toggleTileHuntingOnlyHighlightNewTiles')
    @login_required
    def toggleTileHuntingOnlyHighlightNewTiles():
        redirectUrl = request.args['redirectUrl']
        tileHuntingFilterState = get_tile_hunting_filter_state_by_user(current_user.id)
        currentValue = tileHuntingFilterState.is_only_highlight_new_tiles_active
        tileHuntingFilterState.is_only_highlight_new_tiles_active = not currentValue  # type: ignore[assignment]
        db.session.commit()

        return redirect(redirectUrl)

    @maps.route('/toggleTileHuntingMaxSquare')
    @login_required
    def toggleTileHuntingMaxSquare():
        redirectUrl = request.args['redirectUrl']
        tileHuntingFilterState = get_tile_hunting_filter_state_by_user(current_user.id)
        currentValue = tileHuntingFilterState.is_show_max_square_active
        tileHuntingFilterState.is_show_max_square_active = not currentValue  # type: ignore[assignment]
        db.session.commit()

        return redirect(redirectUrl)

    @maps.route('/toggleTileHuntingShowPlannedTiles')
    @login_required
    def toggleTileHuntingShowPlannedTiles():
        redirectUrl = request.args['redirectUrl']
        tileHuntingFilterState = get_tile_hunting_filter_state_by_user(current_user.id)
        currentValue = tileHuntingFilterState.is_show_planned_tiles_active
        tileHuntingFilterState.is_show_planned_tiles_active = not currentValue  # type: ignore[assignment]
        db.session.commit()

        return redirect(redirectUrl)

    def __create_visited_tile_service(
        quickFilterState: QuickFilterState, tileHuntingFilterState: TileHuntingFilterState
    ) -> VisitedTileService:
        return VisitedTileService(
            newVisitedTileCache,
            maxSquareCache,
            quickFilterState,
            tileHuntingFilterState,
            distanceWorkoutService,
        )

    return maps


def __escape_name(name: str) -> str:
    return name.replace('<', '&lt;').replace('>', '&gt;')
