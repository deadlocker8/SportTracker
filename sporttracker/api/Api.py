import logging
from typing import Any

from flask import Blueprint, jsonify, render_template, redirect, url_for, request, abort
from flask_login import login_required, current_user
from pydantic import ValidationError

from sporttracker.api.FormModels import (
    MonthGoalDistanceApiFormModel,
    MonthGoalCountApiFormModel,
    MonthGoalDurationApiFormModel,
    DistanceWorkoutApiFormModel,
    FitnessWorkoutApiFormModel,
)
from sporttracker.api.Mapper import (
    MAPPER_MONTH_GOAL_DISTANCE,
    MAPPER_MONTH_GOAL_COUNT,
    MAPPER_MONTH_GOAL_DURATION,
    MAPPER_DISTANCE_WORKOUT,
    MAPPER_FITNESS_WORKOUT,
    MAPPER_PARTICIPANT,
    MAPPER_PLANNED_TOUR,
    MAPPER_MAINTENANCE,
    MAPPER_CUSTOM_FIELD,
)
from sporttracker.logic import Constants
from sporttracker.logic.GpxService import GpxService
from sporttracker.logic.MaintenanceEventsCollector import get_maintenances_with_events
from sporttracker.logic.QuickFilterState import QuickFilterState
from sporttracker.logic.model.CustomWorkoutField import get_custom_fields_by_workout_type
from sporttracker.logic.model.DistanceWorkout import DistanceWorkout, get_distance_workout_by_id
from sporttracker.logic.model.FitnessWorkout import FitnessWorkout
from sporttracker.logic.model.FitnessWorkoutCategory import (
    update_workout_categories_by_workout_id,
    FitnessWorkoutCategoryType,
)
from sporttracker.logic.model.FitnessWorkoutType import FitnessWorkoutType
from sporttracker.logic.model.MonthGoal import MonthGoalDistance, MonthGoalCount, MonthGoalDuration
from sporttracker.logic.model.Participant import get_participants, get_participants_by_ids
from sporttracker.logic.model.PlannedTour import get_planned_tours, get_planned_tour_by_id
from sporttracker.logic.model.WorkoutType import WorkoutType
from sporttracker.logic.model.db import db

LOGGER = logging.getLogger(Constants.APP_NAME)

API_VERSION = '2.0.0'


def construct_blueprint(gpxService: GpxService, tileHuntingSettings: dict[str, Any]):
    api = Blueprint('api', __name__, static_folder='static', url_prefix='/api/v2')

    @api.route('/')
    @login_required
    def apiIndex():
        return redirect(url_for('api.docs'))

    @api.route('/version')
    @login_required
    def getVersion():
        return jsonify({'version': API_VERSION})

    @api.route('/docs')
    @login_required
    def docs():
        return render_template('swaggerui/swaggerui.jinja2')

    @api.route('/monthGoals/monthGoalDistance')
    @login_required
    def listMonthGoalDistance():
        monthGoals = (
            MonthGoalDistance.query.filter(MonthGoalDistance.user_id == current_user.id)
            .order_by(MonthGoalDistance.year.asc(), MonthGoalDistance.month.asc())
            .all()
        )

        return jsonify([MAPPER_MONTH_GOAL_DISTANCE.map(m) for m in monthGoals])

    @api.route('/monthGoals/monthGoalDistance', methods=['POST'])
    @login_required
    def addMonthGoalDistance():
        try:
            form = MonthGoalDistanceApiFormModel.model_validate_json(request.data)
        except ValidationError as e:
            return jsonify({'error': str(e)}), 400

        errorMessageWorkoutType = (
            f"workout_type '{form.workout_type}' is not a valid workout type, "
            f'allowed types: {[w.name for w in WorkoutType.get_distance_workout_types()]}'
        )
        try:
            workoutType = WorkoutType(form.workout_type)  # type: ignore[call-arg]
        except ValueError:
            return jsonify({'error': errorMessageWorkoutType}), 400

        if workoutType not in WorkoutType.get_distance_workout_types():
            return jsonify(
                {
                    'error': f"workout_type '{form.workout_type}' is not allowed for distance-based "
                    f'month goals, allowed types: '
                    f'{[w.name for w in WorkoutType.get_distance_workout_types()]}'
                }
            ), 400

        monthGoal = MonthGoalDistance(
            type=workoutType,
            year=form.year,
            month=form.month,
            distance_minimum=form.distance_minimum,
            distance_perfect=form.distance_perfect,
            user_id=current_user.id,
        )

        LOGGER.debug(f'Saved new month goal of type "distance" via api: {monthGoal}')
        db.session.add(monthGoal)
        db.session.commit()

        return {'id': monthGoal.id}, 200

    @api.route('/monthGoals/monthGoalCount')
    @login_required
    def listMonthGoalCount():
        monthGoals = (
            MonthGoalCount.query.filter(MonthGoalCount.user_id == current_user.id)
            .order_by(MonthGoalCount.year.asc(), MonthGoalCount.month.asc())
            .all()
        )

        return jsonify([MAPPER_MONTH_GOAL_COUNT.map(m) for m in monthGoals])

    @api.route('/monthGoals/monthGoalCount', methods=['POST'])
    @login_required
    def addMonthGoalCount():
        try:
            form = MonthGoalCountApiFormModel.model_validate_json(request.data)
        except ValidationError as e:
            return jsonify({'error': str(e)}), 400

        errorMessageWorkoutType = (
            f"workout_type '{form.workout_type}' is not a valid workout type, "
            f'allowed types: {[w.name for w in WorkoutType]}'
        )
        try:
            workoutType = WorkoutType(form.workout_type)  # type: ignore[call-arg]
        except ValueError:
            return jsonify({'error': errorMessageWorkoutType}), 400

        monthGoal = MonthGoalCount(
            type=workoutType,
            year=form.year,
            month=form.month,
            count_minimum=form.count_minimum,
            count_perfect=form.count_perfect,
            user_id=current_user.id,
        )

        LOGGER.debug(f'Saved new month goal of type "count" via api: {monthGoal}')
        db.session.add(monthGoal)
        db.session.commit()

        return {'id': monthGoal.id}, 200

    @api.route('/monthGoals/monthGoalDuration')
    @login_required
    def listMonthGoalDuration():
        monthGoals = (
            MonthGoalDuration.query.filter(MonthGoalDuration.user_id == current_user.id)
            .order_by(MonthGoalDuration.year.asc(), MonthGoalDuration.month.asc())
            .all()
        )

        return jsonify([MAPPER_MONTH_GOAL_DURATION.map(m) for m in monthGoals])

    @api.route('/monthGoals/monthGoalDuration', methods=['POST'])
    @login_required
    def addMonthGoalDuration():
        try:
            form = MonthGoalDurationApiFormModel.model_validate_json(request.data)
        except ValidationError as e:
            return jsonify({'error': str(e)}), 400

        errorMessageWorkoutType = (
            f"workout_type '{form.workout_type}' is not a valid workout type, "
            f'allowed types: {[w.name for w in WorkoutType]}'
        )
        try:
            workoutType = WorkoutType(form.workout_type)  # type: ignore[call-arg]
        except ValueError:
            return jsonify({'error': errorMessageWorkoutType}), 400

        monthGoal = MonthGoalDuration(
            type=workoutType,
            year=form.year,
            month=form.month,
            duration_minimum=form.duration_minimum,
            duration_perfect=form.duration_perfect,
            user_id=current_user.id,
        )

        LOGGER.debug(f'Saved new month goal of type "duration" via api: {monthGoal}')
        db.session.add(monthGoal)
        db.session.commit()

        return {'id': monthGoal.id}, 200

    @api.route('/workouts/distanceWorkout')
    @login_required
    def listDistanceWorkout():
        workouts = (
            DistanceWorkout.query.filter(DistanceWorkout.user_id == current_user.id)
            .order_by(DistanceWorkout.start_time.asc())
            .all()
        )

        return jsonify([MAPPER_DISTANCE_WORKOUT.map(w) for w in workouts])

    @api.route('/workouts/distanceWorkout', methods=['POST'])
    @login_required
    def addDistanceWorkout():
        try:
            form = DistanceWorkoutApiFormModel.model_validate_json(request.data)
        except ValidationError as e:
            return jsonify({'error': str(e)}), 400

        errorMessageWorkoutType = (
            f"workout_type '{form.workout_type}' is not allowed for distance workouts, "
            f'allowed types: {[w.name for w in WorkoutType.get_distance_workout_types()]}'
        )
        try:
            workoutType = WorkoutType(form.workout_type)  # type: ignore[call-arg]
        except ValueError:
            return jsonify({'error': errorMessageWorkoutType}), 400

        if workoutType not in WorkoutType.get_distance_workout_types():
            return jsonify({'error': errorMessageWorkoutType}), 400

        plannedTour = None
        if form.planned_tour_id is not None:
            plannedTour = get_planned_tour_by_id(int(form.planned_tour_id))
            if plannedTour is None:
                return jsonify(
                    {'error': f'No planned tour found for planned_tour_id {form.planned_tour_id}'}
                ), 400

        workout = DistanceWorkout(
            name=form.name,
            type=workoutType,
            start_time=form.calculate_start_time(),
            duration=form.duration,
            distance=form.distance,
            average_heart_rate=form.average_heart_rate,
            elevation_sum=form.elevation_sum,
            custom_fields={} if form.custom_fields is None else form.custom_fields,
            participants=get_participants_by_ids(form.participants),
            planned_tour=plannedTour,
            share_code=None,
            gpx_metadata_id=None,
            user_id=current_user.id,
        )

        LOGGER.debug(f'Saved new distance workout via api: {workout}')
        db.session.add(workout)
        db.session.commit()

        return {'id': workout.id}, 200

    @api.route('/workouts/distanceWorkout/<int:workout_id>/addGpxTrack', methods=['POST'])
    @login_required
    def addGpxTrack(workout_id: int):
        workout = get_distance_workout_by_id(workout_id)

        if workout is None:
            abort(404)

        gpxMetadataId = gpxService.handle_gpx_upload_for_workout(request.files)
        if gpxMetadataId is None:
            abort(400)

        gpxService.delete_gpx(workout, current_user.id)

        workout.gpx_metadata_id = gpxMetadataId
        db.session.add(workout)
        db.session.commit()

        gpxService.add_visited_tiles_for_workout(
            workout, tileHuntingSettings['baseZoomLevel'], current_user.id
        )

        LOGGER.debug(
            f'Added gpx track {workout.get_gpx_metadata().gpx_file_name} to workout {workout.id}'  # type: ignore[union-attr]
        )

        return '', 200

    @api.route('/workouts/fitnessWorkout')
    @login_required
    def listFitnessWorkout():
        workouts = (
            FitnessWorkout.query.filter(FitnessWorkout.user_id == current_user.id)
            .order_by(FitnessWorkout.start_time.asc())
            .all()
        )

        return jsonify([MAPPER_FITNESS_WORKOUT.map(w) for w in workouts])

    @api.route('/workouts/fitnessWorkout', methods=['POST'])
    @login_required
    def addFitnessWorkout():
        try:
            form = FitnessWorkoutApiFormModel.model_validate_json(request.data)
        except ValidationError as e:
            return jsonify({'error': str(e)}), 400

        errorMessageWorkoutType = (
            f"workout_type '{form.workout_type}' is not allowed for fitness workouts, "
            f'allowed types: {[w.name for w in WorkoutType.get_fitness_workout_types()]}'
        )
        try:
            workoutType = WorkoutType(form.workout_type)  # type: ignore[call-arg]
        except ValueError:
            return jsonify({'error': errorMessageWorkoutType}), 400

        if workoutType not in WorkoutType.get_fitness_workout_types():
            return jsonify({'error': errorMessageWorkoutType}), 400

        try:
            fitnessWorkoutType = FitnessWorkoutType(form.fitness_workout_type)  # type: ignore[call-arg]
        except ValueError:
            return jsonify(
                {
                    'error': f"fitness_workout_type '{form.fitness_workout_type}' is not a valid type, "
                    f'allowed types: {[w.name for w in FitnessWorkoutType]}'
                }
            ), 400

        fitnessWorkoutCategories = []
        if form.fitness_workout_categories is not None:
            for category in form.fitness_workout_categories:
                try:
                    fitnessWorkoutCategories.append(FitnessWorkoutCategoryType(category))  # type: ignore[call-arg]
                except ValueError:
                    return jsonify(
                        {
                            'error': f"fitness_workout_categories contain invalid type '{category}', "
                            f'allowed types: {[w.name for w in FitnessWorkoutCategoryType]}'
                        }
                    ), 400

        workout = FitnessWorkout(
            name=form.name,
            type=workoutType,
            start_time=form.calculate_start_time(),
            duration=form.duration,
            average_heart_rate=form.average_heart_rate,
            custom_fields={} if form.custom_fields is None else form.custom_fields,
            participants=get_participants_by_ids(form.participants),
            fitness_workout_type=fitnessWorkoutType,
            user_id=current_user.id,
        )

        LOGGER.debug(f'Saved new distance workout via api: {workout}')
        db.session.add(workout)
        db.session.commit()

        if fitnessWorkoutCategories:
            update_workout_categories_by_workout_id(workout.id, fitnessWorkoutCategories)

        return {'id': workout.id}, 200

    @api.route('/settings/participants')
    @login_required
    def listParticipants():
        participants = get_participants()
        return jsonify([MAPPER_PARTICIPANT.map(p) for p in participants])

    @api.route('/settings/customFields')
    @login_required
    def listCustomFields():
        customFields = get_custom_fields_by_workout_type()

        result = {}
        for workoutType, fields in customFields.items():
            result[workoutType.name] = [MAPPER_CUSTOM_FIELD.map(f) for f in fields]

        return jsonify(result)

    @api.route('/plannedTours')
    @login_required
    def listPlannedTours():
        plannedTours = get_planned_tours(WorkoutType.get_distance_workout_types())
        return jsonify([MAPPER_PLANNED_TOUR.map(p) for p in plannedTours])

    @api.route('/maintenances')
    @login_required
    def listMaintenances():
        maintenancesWithEvents = get_maintenances_with_events(QuickFilterState())
        return jsonify([MAPPER_MAINTENANCE.map(m) for m in maintenancesWithEvents])

    return api
