import io
import logging
from datetime import datetime, timedelta
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
    jsonify,
    Response,
)
from flask_login import login_required, current_user
from sqlalchemy import func, and_, or_

from sporttracker import Constants
from sporttracker.db import db
from sporttracker.gpx.GpxService import GpxService, GpxParser
from sporttracker.helpers import DateFormats
from sporttracker.longDistanceTour.LongDistanceTourBlueprint import LongDistanceTourModel
from sporttracker.longDistanceTour.LongDistanceTourService import LongDistanceTourService
from sporttracker.plannedTour.PlannedTourBlueprint import PlannedTourModel
from sporttracker.plannedTour.PlannedTourFilterStateEntity import get_planned_tour_filter_state_by_user
from sporttracker.plannedTour.PlannedTourService import PlannedTourService
from sporttracker.quickFilter.QuickFilterStateEntity import get_quick_filter_state_by_user, QuickFilterState
from sporttracker.tileHunting.BoundingBox import BoundingBox
from sporttracker.tileHunting.Colors import (
    COLOR_PLANNED,
    Color,
)
from sporttracker.tileHunting.MaxSquareCache import MaxSquareCache
from sporttracker.tileHunting.NewVisitedTileCache import NewVisitedTileCache
from sporttracker.tileHunting.TileHuntingFilterStateEntity import (
    get_tile_hunting_filter_state_by_user,
    TileHuntingFilterState,
)
from sporttracker.tileHunting.TileRenderService import TileRenderService
from sporttracker.tileHunting.VisitedTileService import VisitedTileService
from sporttracker.user.UserEntity import get_user_by_tile_hunting_shared_code
from sporttracker.workout.WorkoutModel import DistanceWorkoutModel
from sporttracker.workout.WorkoutService import WorkoutService
from sporttracker.workout.WorkoutType import WorkoutType
from sporttracker.workout.distance.DistanceWorkoutEntity import DistanceWorkout
from sporttracker.workout.distance.DistanceWorkoutService import DistanceWorkoutService

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
        'workoutName': f'{workoutStartTime.strftime(DateFormats.DATE_FORMAT_DATE)} - {__escape_name(workoutName)}',
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
        query = (
            DistanceWorkout.query.with_entities(
                func.max(DistanceWorkout.id),
                DistanceWorkout.name,
                funcStartTime,
                func.max(DistanceWorkout.type),
            )
            .filter(DistanceWorkout.user_id == current_user.id)
            .filter(DistanceWorkout.gpx_metadata_id.isnot(None))
            .filter(DistanceWorkout.type.in_(quickFilterState.get_active_distance_workout_types()))
            .group_by(DistanceWorkout.name)
            .order_by(funcStartTime.desc())
        )

        dateRanges = quickFilterState.get_effective_date_ranges()
        if dateRanges:
            query = query.filter(
                or_(
                    *(
                        and_(
                            DistanceWorkout.start_time >= dateFrom,
                            DistanceWorkout.start_time < dateTo + timedelta(days=1),
                        )
                        for dateFrom, dateTo in dateRanges
                    )
                )
            )

        workouts = query.all()

        for workout in workouts:
            workoutId, workoutName, workoutStartTime, workoutType = workout
            gpxInfo.append(createGpxInfo(workoutId, workoutName, workoutStartTime, workoutType))

        return render_template(
            'map/mapMultipleWorkouts.jinja2',
            gpxInfo=gpxInfo,
            quickFilterState=quickFilterState,
            mapMode='workouts',
            redirectUrl='maps.showAllWorkoutsOnMap',
        )

    @maps.route('/map/<int:workout_id>')
    @login_required
    def showSingleWorkout(workout_id: int):
        workout = distanceWorkoutService.get_distance_workout_by_id(workout_id, current_user.id)

        if workout is None:
            abort(404)

        tileHuntingNumberOfNewVisitedTiles = 0

        quickFilterState = QuickFilterState().reset(WorkoutService.get_available_years(current_user.id))

        tileHuntingFilterState = get_tile_hunting_filter_state_by_user(current_user.id)
        visitedTileService = __create_visited_tile_service(quickFilterState, tileHuntingFilterState)
        newVisitedTilesPerWorkout = visitedTileService.get_number_of_new_tiles_per_workout()
        filtered = [x for x in newVisitedTilesPerWorkout if x.distance_workout_id == workout_id]
        if filtered:
            tileHuntingNumberOfNewVisitedTiles = filtered[0].numberOfNewTiles

        return render_template(
            'map/mapSingleWorkout.jinja2',
            workout=DistanceWorkoutModel.create_from_workout(workout),
            gpxUrl=url_for(
                'gpxTracks.downloadGpxTrackByWorkoutId',
                workout_id=workout_id,
                file_format=GpxService.GPX_FILE_EXTENSION,
            ),
            editUrl=url_for('distanceWorkouts.edit', workout_id=workout_id),
            tileRenderUrl=url_for('maps.tileOverlay'),
            tileHuntingFilterState=get_tile_hunting_filter_state_by_user(current_user.id),
            tileHuntingNumberOfNewVisitedTiles=tileHuntingNumberOfNewVisitedTiles,
        )

    @maps.route('/map/shared/<string:shareCode>')
    def showSharedSingleWorkout(shareCode: str):
        workout = distanceWorkoutService.get_distance_workout_by_share_code(shareCode)

        if workout is None:
            return render_template('map/mapNotFound.jinja2', errorText=flask_babel.gettext('Unknown shared link'))

        return render_template(
            'map/mapSingleWorkout.jinja2',
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
            return render_template('map/mapNotFound.jinja2', errorText=flask_babel.gettext('Unknown planned tour'))

        return render_template(
            'map/mapPlannedTour.jinja2',
            plannedTour=PlannedTourModel.create_from_tour(plannedTour, True),
            gpxUrl=url_for(
                'gpxTracks.downloadGpxTrackByPlannedTourId',
                tour_id=tour_id,
                file_format=GpxService.GPX_FILE_EXTENSION,
            ),
            editUrl=url_for('plannedTours.edit', tour_id=tour_id),
            tileRenderUrl=url_for('maps.tileOverlay'),
            tileHuntingFilterState=get_tile_hunting_filter_state_by_user(current_user.id),
            tileHuntingNumberOfNewVisitedTiles=plannedTourService.get_number_of_new_visited_tiles(plannedTour),
            maxSquareColor=tileHuntingSettings['maxSquareColor'],
            plannedTileColor=COLOR_PLANNED.to_hex(),
        )

    @maps.route('/map/plannedTour/shared/<string:shareCode>')
    def showSharedPlannedTour(shareCode: str):
        plannedTour = PlannedTourService.get_planned_tour_by_share_code(shareCode)

        if plannedTour is None:
            return render_template('map/mapNotFound.jinja2', errorText=flask_babel.gettext('Unknown shared link'))

        return render_template(
            'map/mapPlannedTour.jinja2',
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
            'map/mapMultipleWorkouts.jinja2',
            gpxInfo=gpxInfo,
            quickFilterState=quickFilterState,
            mapMode='plannedTours',
            redirectUrl='maps.showAllPlannedToursOnMap',
            tileHuntingFilterState=get_tile_hunting_filter_state_by_user(current_user.id),
            tileRenderUrl=url_for('maps.tileOverlay'),
            plannedTourFilterState=plannedTourFilterState,
            maxSquareColor=tileHuntingSettings['maxSquareColor'],
            plannedTileColor=COLOR_PLANNED.to_hex(),
        )

    @maps.route('/map/tileOverlay', methods=['GET'])
    @login_required
    def tileOverlay():
        bbox = request.args.get('bbox')
        if not bbox:
            return jsonify({'type': 'FeatureCollection', 'features': []})

        mode = request.args.get('mode', 'workoutTypes')
        workout_id = request.args.get('workout_id', None, type=int)

        base_zoom = tileHuntingSettings['baseZoomLevel']

        bounding_box = __calculate_bounding_box(bbox, base_zoom)
        if bounding_box is None:
            return jsonify({'type': 'FeatureCollection', 'features': []})

        quickFilterState = get_quick_filter_state_by_user(current_user.id)
        if mode == 'heatmap':
            quickFilterState.enable_all_workout_types()

        tileHuntingFilterState = get_tile_hunting_filter_state_by_user(current_user.id)
        visitedTileService = __create_visited_tile_service(
            quickFilterState, tileHuntingFilterState, workoutId=workout_id
        )

        if mode == 'heatmap':
            visit_counts_by_position = visitedTileService.determine_number_of_visits(
                bounding_box.x_min, bounding_box.x_max, bounding_box.y_min, bounding_box.y_max, current_user.id
            )

            features = []
            for (x, y), count in visit_counts_by_position.items():
                color = TileRenderService.calculate_heatmap_color(count)
                features.append(GpxParser.create_geojson_feature(x, y, base_zoom, color))
        else:
            tile_color_by_position = visitedTileService.determine_tile_colors_of_workouts_that_visit_tiles(
                bounding_box.x_min, bounding_box.x_max, bounding_box.y_min, bounding_box.y_max, current_user.id
            )

            planned_tiles = visitedTileService.determine_planned_tiles(
                bounding_box.x_min, bounding_box.x_max, bounding_box.y_min, bounding_box.y_max, current_user.id
            )

            max_square_positions: set[tuple[int, int]] = set()
            if workout_id is None and tileHuntingFilterState.is_show_max_square_active:
                max_square_positions = set(visitedTileService.get_max_square_tile_positions())

            max_square_color = Color.from_hex(tileHuntingSettings['maxSquareColor'])

            features = []
            for (x, y), color in tile_color_by_position.items():
                if (x, y) in max_square_positions:
                    color = max_square_color

                features.append(GpxParser.create_geojson_feature(x, y, base_zoom, color))

            for pt in planned_tiles:
                key = (pt.x, pt.y)

                if key in tile_color_by_position:
                    continue
                if key in max_square_positions:
                    continue

                features.append(GpxParser.create_geojson_feature(pt.x, pt.y, base_zoom, COLOR_PLANNED))

        return jsonify({'type': 'FeatureCollection', 'features': features})

    @maps.route('/map/tileOverlay/<string:share_code>/<int:zoom>/<int:x>/<int:y>.png', methods=['GET'])
    def renderAllTileHuntingTilesViaShareCode(share_code: str, zoom: int, x: int, y: int):
        user = get_user_by_tile_hunting_shared_code(share_code)
        if user is None:
            abort(404)

        tileHuntingFilterState = TileHuntingFilterState().reset()
        tileHuntingFilterState.is_show_max_square_active = False  # type: ignore[assignment]
        tileHuntingFilterState.is_show_planned_tiles_active = user.isTileHuntingShowPlannedTilesActivated  # type: ignore[assignment]

        visitedTileService = __create_visited_tile_service(
            QuickFilterState().reset(WorkoutService.get_available_years(user.id)), tileHuntingFilterState
        )
        tileRenderService = TileRenderService(tileHuntingSettings['baseZoomLevel'], 256, visitedTileService)

        borderColor = ImageColor.getcolor(tileHuntingSettings['borderColor'], 'RGBA')
        image = tileRenderService.render_image(
            x,
            y,
            zoom,
            user.id,
            borderColor,  # type: ignore[arg-type]
        )

        with io.BytesIO() as output:
            image.save(output, format='PNG')
            return Response(output.getvalue(), mimetype='image/png')

    @maps.route('/map/tileHunting')
    @login_required
    def showTileHuntingMap():
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
            'map/mapTileHunting.jinja2',
            quickFilterState=quickFilterState,
            redirectUrl='maps.showTileHuntingMap',
            tileRenderUrl=url_for('maps.tileOverlay'),
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
            'maps.tileOverlay',
            mode='heatmap',
            _external=True,
        )

        numberOfVisitsUrl = url_for(
            'maps.getNumberOfVisitsByCoordinate',
            user_id=current_user.id,
            latitude=0,
            longitude=0,
            zoom=0,
        )
        numberOfVisitsUrl = numberOfVisitsUrl.split('/0.0/0.0')[0]

        quickFilterState = get_quick_filter_state_by_user(current_user.id)

        return render_template(
            'map/mapTileHuntingHeatmap.jinja2',
            quickFilterState=quickFilterState,
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

        quickFilterState = get_quick_filter_state_by_user(user_id)
        quickFilterState.enable_all_workout_types()

        tileHuntingFilterState = get_tile_hunting_filter_state_by_user(current_user.id)
        visitedTileService = __create_visited_tile_service(quickFilterState, tileHuntingFilterState)
        visit_counts_by_position = visitedTileService.determine_number_of_visits(
            visitedTile.x, visitedTile.x, visitedTile.y, visitedTile.y, user_id
        )
        numberOfVisits = 0
        if visit_counts_by_position:
            numberOfVisits = visit_counts_by_position[(visitedTile.x, visitedTile.y)]

        return jsonify({'numberOfVisits': numberOfVisits})

    @maps.route('/map/longDistanceTour/<int:tour_id>')
    @login_required
    def showLongDistanceTour(tour_id: int):
        longDistanceTour = LongDistanceTourService.get_long_distance_tour_by_id(tour_id)

        if longDistanceTour is None:
            return render_template(
                'map/mapNotFound.jinja2', errorText=flask_babel.gettext('Unknown long-distance tour')
            )

        longDistanceTourModel = LongDistanceTourModel.create_from_tour(longDistanceTour)

        gpxInfo = []
        for order, tour in enumerate(longDistanceTourModel.linkedPlannedTours):
            tourName = f'{flask_babel.gettext("Stage")} {order + 1} - {tour.name}'
            gpxInfo.append(
                createGpxInfoPlannedTour(tour.id, tourName, url_for('maps.showPlannedTour', tour_id=tour.id))
            )  # type: ignore[arg-type]

        return render_template(
            'map/mapLongDistanceTour.jinja2',
            longDistanceTour=longDistanceTourModel,
            gpxInfo=gpxInfo,
            editUrl=url_for('longDistanceTours.edit', tour_id=tour_id),
            tileRenderUrl=url_for('maps.tileOverlay'),
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
        quickFilterState: QuickFilterState,
        tileHuntingFilterState: TileHuntingFilterState,
        workoutId: int | None = None,
    ) -> VisitedTileService:
        return VisitedTileService(
            newVisitedTileCache,
            maxSquareCache,
            quickFilterState,
            tileHuntingFilterState,
            distanceWorkoutService,
            workoutId=workoutId,
        )

    def __calculate_bounding_box(bbox: str, base_zoom: int) -> BoundingBox | None:
        try:
            parts = bbox.split(',')
            min_lng, min_lat, max_lng, max_lat = [float(p) for p in parts]
        except (ValueError, IndexError):
            return None

        tile_nw = GpxParser.convert_coordinate_to_tile_position(max_lat, min_lng, base_zoom)
        tile_se = GpxParser.convert_coordinate_to_tile_position(min_lat, max_lng, base_zoom)

        return BoundingBox(
            x_min=min(tile_nw.x, tile_se.x),
            x_max=max(tile_nw.x, tile_se.x),
            y_min=min(tile_nw.y, tile_se.y),
            y_max=max(tile_nw.y, tile_se.y),
        )

    return maps


def __escape_name(name: str) -> str:
    return name.replace('<', '&lt;').replace('>', '&gt;')
