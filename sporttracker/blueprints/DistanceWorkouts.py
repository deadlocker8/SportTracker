import logging
import uuid
from typing import Any

from flask import Blueprint, render_template, abort, redirect, url_for, request
from flask_login import login_required, current_user
from flask_pydantic import validate
from pydantic import ConfigDict, field_validator

from sporttracker.blueprints.Workouts import BaseWorkoutFormModel
from sporttracker.logic import Constants
from sporttracker.logic.GpxService import GpxService
from sporttracker.logic.model.CustomWorkoutField import CustomWorkoutField
from sporttracker.logic.model.DistanceWorkout import (
    DistanceWorkout,
    get_distance_workout_by_id,
)
from sporttracker.logic.model.Participant import get_participants_by_ids, get_participants
from sporttracker.logic.model.PlannedTour import get_planned_tours, get_planned_tour_by_id
from sporttracker.logic.model.Workout import get_workout_names_by_type
from sporttracker.logic.model.WorkoutType import WorkoutType
from sporttracker.logic.model.db import db

LOGGER = logging.getLogger(Constants.APP_NAME)


class DistanceWorkoutFormModel(BaseWorkoutFormModel):
    distance: float
    plannedTourId: str = '-1'
    averageHeartRate: int | None = None
    elevationSum: int | None = None
    gpxFileName: str | None = None
    hasFitFile: bool = False
    shareCode: str | None = None

    model_config = ConfigDict(
        extra='allow',
    )

    @field_validator(*['averageHeartRate', 'elevationSum'], mode='before')
    def averageHeartRateCheck(cls, value: str, info) -> str | None:
        if isinstance(value, str):
            value = value.strip()
        if value == '':
            return None
        return value


def construct_blueprint(gpxService: GpxService, tileHuntingSettings: dict[str, Any]):
    distanceWorkouts = Blueprint(
        'distanceWorkouts', __name__, static_folder='static', url_prefix='/distanceWorkouts'
    )

    @distanceWorkouts.route('/post', methods=['POST'])
    @login_required
    @validate()
    def addPost(form: DistanceWorkoutFormModel):
        gpxMetadataId = gpxService.handle_gpx_upload_for_workout(request.files)

        participantIds = [int(item) for item in request.form.getlist('participants')]
        participants = get_participants_by_ids(participantIds)
        if form.plannedTourId == '-1':
            plannedTour = None
        else:
            plannedTour = get_planned_tour_by_id(int(form.plannedTourId))

        workout = DistanceWorkout(
            name=form.name,
            type=WorkoutType(form.type),  # type: ignore[call-arg]
            start_time=form.calculate_start_time(),
            duration=form.calculate_duration(),
            distance=form.distance * 1000,
            average_heart_rate=form.averageHeartRate,
            elevation_sum=form.elevationSum,
            gpx_metadata_id=gpxMetadataId,
            custom_fields=form.model_extra,
            user_id=current_user.id,
            participants=participants,
            share_code=form.shareCode if form.shareCode else None,
            planned_tour=plannedTour,
        )

        LOGGER.debug(f'Saved new distance workout: {workout}')
        db.session.add(workout)
        db.session.commit()

        if gpxMetadataId is not None:
            gpxService.add_visited_tiles_for_workout(
                workout, tileHuntingSettings['baseZoomLevel'], current_user.id
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

        gpxFileName = None
        gpxMetadata = workout.get_gpx_metadata()
        if gpxMetadata is not None:
            gpxFileName = gpxMetadata.gpx_file_name

        workoutModel = DistanceWorkoutFormModel(
            name=workout.name,  # type: ignore[arg-type]
            type=workout.type,
            date=workout.start_time.strftime('%Y-%m-%d'),  # type: ignore[attr-defined]
            time=workout.start_time.strftime('%H:%M'),  # type: ignore[attr-defined]
            distance=workout.distance / 1000,
            durationHours=workout.duration // 3600,
            durationMinutes=workout.duration % 3600 // 60,
            durationSeconds=workout.duration % 3600 % 60,
            averageHeartRate=workout.average_heart_rate,
            elevationSum=workout.elevation_sum,
            gpxFileName=gpxFileName,
            hasFitFile=gpxService.has_fit_file(gpxFileName),
            participants=[str(item.id) for item in workout.participants],
            shareCode=workout.share_code,
            plannedTourId=str(workout.planned_tour.id) if workout.planned_tour else '-1',
            **workout.custom_fields,
        )

        customFields = (
            CustomWorkoutField.query.filter(CustomWorkoutField.user_id == current_user.id)
            .filter(CustomWorkoutField.workout_type == workout.type)
            .all()
        )

        return render_template(
            f'workouts/workout{workout.type.name.capitalize()}Form.jinja2',
            workout=workoutModel,
            workout_id=workout_id,
            customFields=customFields,
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

        if form.plannedTourId == '-1':
            plannedTour = None
        else:
            plannedTour = get_planned_tour_by_id(int(form.plannedTourId))

        workout.name = form.name  # type: ignore[assignment]
        workout.start_time = form.calculate_start_time()  # type: ignore[assignment]
        workout.distance = form.distance * 1000  # type: ignore[assignment]
        workout.duration = form.calculate_duration()  # type: ignore[assignment]
        workout.average_heart_rate = form.averageHeartRate  # type: ignore[assignment]
        workout.elevation_sum = form.elevationSum  # type: ignore[assignment]
        participantIds = [int(item) for item in request.form.getlist('participants')]
        workout.participants = get_participants_by_ids(participantIds)
        workout.share_code = form.shareCode if form.shareCode else None  # type: ignore[assignment]
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
            'url': url_for('maps.showSharedSingleTrack', shareCode=shareCode, _external=True),
            'shareCode': shareCode,
        }

    return distanceWorkouts
