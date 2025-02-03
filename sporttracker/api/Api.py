import logging

from flask import Blueprint, jsonify, render_template, redirect, url_for
from flask_login import login_required, current_user

from sporttracker.api.Mapper import (
    MAPPER_MONTH_GOAL_DISTANCE,
    MAPPER_MONTH_GOAL_COUNT,
    MAPPER_MONTH_GOAL_DURATION,
    MAPPER_DISTANCE_WORKOUT,
    MAPPER_FITNESS_WORKOUT,
    MAPPER_PARTICIPANT,
    MAPPER_PLANNED_TOUR,
    MAPPER_MAINTENANCE,
)
from sporttracker.logic import Constants
from sporttracker.logic.MaintenanceEventsCollector import get_maintenances_with_events
from sporttracker.logic.QuickFilterState import QuickFilterState
from sporttracker.logic.model.DistanceWorkout import DistanceWorkout
from sporttracker.logic.model.FitnessWorkout import FitnessWorkout
from sporttracker.logic.model.MonthGoal import MonthGoalDistance, MonthGoalCount, MonthGoalDuration
from sporttracker.logic.model.Participant import get_participants
from sporttracker.logic.model.PlannedTour import get_planned_tours
from sporttracker.logic.model.WorkoutType import WorkoutType

LOGGER = logging.getLogger(Constants.APP_NAME)

API_VERSION = '2.0.0'


def construct_blueprint():
    api = Blueprint('api', __name__, static_folder='static', url_prefix='/api')

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

    @api.route('/monthGoals/monthGoalCount')
    @login_required
    def listMonthGoalCount():
        monthGoals = (
            MonthGoalCount.query.filter(MonthGoalCount.user_id == current_user.id)
            .order_by(MonthGoalCount.year.asc(), MonthGoalCount.month.asc())
            .all()
        )

        return jsonify([MAPPER_MONTH_GOAL_COUNT.map(m) for m in monthGoals])

    @api.route('/monthGoals/monthGoalDuration')
    @login_required
    def listMonthGoalDuration():
        monthGoals = (
            MonthGoalDuration.query.filter(MonthGoalDuration.user_id == current_user.id)
            .order_by(MonthGoalDuration.year.asc(), MonthGoalDuration.month.asc())
            .all()
        )

        return jsonify([MAPPER_MONTH_GOAL_DURATION.map(m) for m in monthGoals])

    @api.route('/workouts/distanceWorkout')
    @login_required
    def listDistanceWorkout():
        workouts = (
            DistanceWorkout.query.filter(DistanceWorkout.user_id == current_user.id)
            .order_by(DistanceWorkout.start_time.asc())
            .all()
        )

        return jsonify([MAPPER_DISTANCE_WORKOUT.map(w) for w in workouts])

    @api.route('/workouts/fitnessWorkout')
    @login_required
    def listFitnessWorkout():
        workouts = (
            FitnessWorkout.query.filter(FitnessWorkout.user_id == current_user.id)
            .order_by(FitnessWorkout.start_time.asc())
            .all()
        )

        return jsonify([MAPPER_FITNESS_WORKOUT.map(w) for w in workouts])

    @api.route('/settings/participants')
    @login_required
    def listParticipants():
        participants = get_participants()

        return jsonify([MAPPER_PARTICIPANT.map(p) for p in participants])

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
