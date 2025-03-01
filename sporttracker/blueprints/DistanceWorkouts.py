import logging
import os
import uuid
from gettext import gettext
from typing import Any

from flask import Blueprint, render_template, abort, redirect, url_for, request, session
from flask_login import login_required, current_user
from flask_pydantic import validate

from sporttracker.blueprints.Workouts import BaseWorkoutFormModel
from sporttracker.logic import Constants
from sporttracker.logic.FitSessionParser import FitSessionParser, FitSession
from sporttracker.logic.GpxService import GpxService
from sporttracker.logic.model.CustomWorkoutField import get_custom_fields_by_workout_type
from sporttracker.logic.model.DistanceWorkout import (
    get_distance_workout_by_id,
)
from sporttracker.logic.model.Participant import get_participants_by_ids, get_participants
from sporttracker.logic.model.PlannedTour import get_planned_tours, get_planned_tour_by_id
from sporttracker.logic.model.Workout import get_workout_names_by_type
from sporttracker.logic.model.db import db
from sporttracker.logic.service.DistanceWorkoutService import (
    DistanceWorkoutService,
    DistanceWorkoutFormModel,
)

LOGGER = logging.getLogger(Constants.APP_NAME)


class DistanceWorkoutImportFromFitModel(BaseWorkoutFormModel):
    distance: float | None
    elevation_sum: int | None = None
    gpx_file_name: str | None = None
    has_fit_file: bool = False


def construct_blueprint(
    gpxService: GpxService,
    tileHuntingSettings: dict[str, Any],
    tempFolderPath: str,
    distanceWorkoutService: DistanceWorkoutService,
):
    distanceWorkouts = Blueprint(
        'distanceWorkouts', __name__, static_folder='static', url_prefix='/distanceWorkouts'
    )

    @distanceWorkouts.route('/post', methods=['POST'])
    @login_required
    @validate()
    def addPost(form_model: DistanceWorkoutFormModel):
        participant_ids = [int(item) for item in request.form.getlist('participants')]
        workout = distanceWorkoutService.add_workout(
            form_model=form_model,
            files=request.files,
            participant_ids=participant_ids,
            user_id=current_user.id,
        )

        return redirect(
            url_for(
                'workouts.listWorkouts',
                year=workout.start_time.year,  # type: ignore[attr-defined]
                month=workout.start_time.month,  # type: ignore[attr-defined]
            )
        )

    @distanceWorkouts.route('/edit/<int:workout_id>')
    @login_required
    def edit(workout_id: int):
        workout = get_distance_workout_by_id(workout_id)

        if workout is None:
            abort(404)

        gpx_file_name = None
        gpxMetadata = workout.get_gpx_metadata()
        if gpxMetadata is not None:
            gpx_file_name = gpxMetadata.gpx_file_name

        workoutModel = DistanceWorkoutFormModel(
            name=workout.name,  # type: ignore[arg-type]
            type=workout.type,
            date=workout.start_time.strftime('%Y-%m-%d'),  # type: ignore[attr-defined]
            time=workout.start_time.strftime('%H:%M'),  # type: ignore[attr-defined]
            distance=workout.distance / 1000,
            duration_hours=workout.duration // 3600,
            duration_minutes=workout.duration % 3600 // 60,
            duration_seconds=workout.duration % 3600 % 60,
            average_heart_rate=workout.average_heart_rate,
            elevation_sum=workout.elevation_sum,
            gpx_file_name=gpx_file_name,
            has_fit_file=gpxService.has_fit_file(gpx_file_name),
            participants=[str(item.id) for item in workout.participants],
            share_code=workout.share_code,
            planned_tour_id=str(workout.planned_tour.id) if workout.planned_tour else '-1',
            **workout.custom_fields,
        )

        return render_template(
            f'workouts/workout{workout.type.name.capitalize()}Form.jinja2',
            workout=workoutModel,
            workout_id=workout_id,
            customFields=get_custom_fields_by_workout_type(workout.type),
            participants=get_participants(),
            workoutNames=get_workout_names_by_type(workout.type),
            plannedTours=get_planned_tours([workout.type]),
        )

    @distanceWorkouts.route('/edit/<int:workout_id>', methods=['POST'])
    @login_required
    @validate()
    def editPost(workout_id: int, form: DistanceWorkoutFormModel):
        workout = get_distance_workout_by_id(workout_id)

        if workout is None:
            abort(404)

        if form.planned_tour_id == '-1':
            plannedTour = None
        else:
            plannedTour = get_planned_tour_by_id(int(form.planned_tour_id))

        workout.name = form.name  # type: ignore[assignment]
        workout.start_time = form.calculate_start_time()  # type: ignore[assignment]
        workout.distance = form.distance * 1000  # type: ignore[assignment]
        workout.duration = form.calculate_duration()  # type: ignore[assignment]
        workout.average_heart_rate = form.average_heart_rate  # type: ignore[assignment]
        workout.elevation_sum = form.elevation_sum  # type: ignore[assignment]
        participantIds = [int(item) for item in request.form.getlist('participants')]
        workout.participants = get_participants_by_ids(participantIds)
        workout.share_code = form.share_code if form.share_code else None  # type: ignore[assignment]
        workout.planned_tour = plannedTour  # type: ignore[assignment]

        shouldUpdateVisitedTiles = False
        newGpxMetadataId = gpxService.handle_gpx_upload_for_workout(request.files)
        if workout.gpx_metadata_id is None:
            workout.gpx_metadata_id = newGpxMetadataId
            shouldUpdateVisitedTiles = True
        else:
            if newGpxMetadataId is not None:
                gpxService.delete_gpx(workout, current_user.id)
                workout.gpx_metadata_id = newGpxMetadataId
                shouldUpdateVisitedTiles = True

        workout.custom_fields = form.model_extra

        db.session.commit()

        if shouldUpdateVisitedTiles and workout.gpx_metadata_id is not None:
            gpxService.add_visited_tiles_for_workout(
                workout, tileHuntingSettings['baseZoomLevel'], current_user.id
            )

        LOGGER.debug(f'Updated distance workout: {workout}')

        return redirect(
            url_for(
                'workouts.listWorkouts',
                year=workout.start_time.year,  # type: ignore[attr-defined]
                month=workout.start_time.month,  # type: ignore[attr-defined]
            )
        )

    @distanceWorkouts.route('/delete/<int:workout_id>')
    @login_required
    def delete(workout_id: int):
        workout = get_distance_workout_by_id(workout_id)

        if workout is None:
            abort(404)

        gpxService.delete_gpx(workout, current_user.id)

        LOGGER.debug(f'Deleted distance workout: {workout}')
        db.session.delete(workout)
        db.session.commit()

        return redirect(url_for('workouts.listWorkouts'))

    @distanceWorkouts.route('/createShareCode')
    @login_required
    def createShareCode():
        shareCode = uuid.uuid4().hex
        return {
            'url': url_for('maps.showSharedSingleWorkout', shareCode=shareCode, _external=True),
            'shareCode': shareCode,
        }

    @distanceWorkouts.route('/importFromFitFile', methods=['POST'])
    @login_required
    def importFromFitFilePost():
        baseErrorMessage = gettext('Error importing data from FIT file')

        file = request.files.get('fitFile', None)
        if file is None or file.filename == '' or file.filename is None:
            return f'{baseErrorMessage}: {gettext("No file provided")}', 400

        if not GpxService.is_allowed_file(file.filename, [GpxService.FIT_FILE_EXTENSION]):
            return (
                f'{baseErrorMessage}: {gettext("Invalid file extension. Allowed extension: *.fit")}',
                400,
            )

        filename = uuid.uuid4().hex
        os.makedirs(tempFolderPath, exist_ok=True)
        fitFilePath = os.path.join(tempFolderPath, f'{filename}.{GpxService.FIT_FILE_EXTENSION}')
        file.save(fitFilePath)
        LOGGER.debug(f'Saved imported FIT file "{file.filename}" to "{fitFilePath}"')

        try:
            LOGGER.debug(f'Parsing session from FIT file "{fitFilePath}"')
            fitSession = FitSessionParser.parse(fitFilePath)
        except Exception as e:
            LOGGER.error(f'Error parsing session from FIT file: "{fitFilePath}": {e}')
            os.remove(fitFilePath)
            return f'{baseErrorMessage}: {str(e)}', 400

        if fitSession is None:
            os.remove(fitFilePath)
            return f'{baseErrorMessage}: {gettext("FIT file does not contain session data")}', 400

        session['fitSession'] = fitSession.to_json()

        return ''

    @distanceWorkouts.route('/importFromFitFile', methods=['GET'])
    @login_required
    def importFromFitFileGet():
        if 'fitSession' not in session:
            return redirect(url_for('workouts.add'))

        fitSession = FitSession.from_json(session['fitSession'])

        workoutFromFitImportModel = DistanceWorkoutImportFromFitModel(
            name='',
            type=fitSession.workout_type.name,
            date=fitSession.start_time.strftime('%Y-%m-%d'),  # type: ignore[attr-defined]
            time=fitSession.start_time.strftime('%H:%M'),  # type: ignore[attr-defined]
            distance=None if fitSession.distance is None else fitSession.distance / 1000,
            duration_hours=fitSession.duration // 3600,
            duration_minutes=fitSession.duration % 3600 // 60,
            duration_seconds=fitSession.duration % 3600 % 60,
            average_heart_rate=fitSession.average_heart_rate,
            elevation_sum=fitSession.total_ascent,
            gpx_file_name=fitSession.file_name,
            has_fit_file=True,
            participants=[],
        )

        return render_template(
            f'workouts/workout{fitSession.workout_type.name.capitalize()}Form.jinja2',
            workoutFromFitImport=workoutFromFitImportModel,
            customFields=get_custom_fields_by_workout_type(fitSession.workout_type),
            participants=get_participants(),
            workoutNames=get_workout_names_by_type(fitSession.workout_type),
            plannedTours=get_planned_tours([fitSession.workout_type]),
        )

    return distanceWorkouts
