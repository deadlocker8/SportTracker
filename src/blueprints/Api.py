import logging

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from pydantic import ValidationError

from blueprints.BikingTracks import BikingTrackFormModel
from blueprints.MonthGoalsCount import MonthGoalCountFormModel
from blueprints.MonthGoalsDistance import MonthGoalDistanceFormModel
from blueprints.RunningTracks import RunningTrackFormModel
from logic import Constants
from logic.model.Models import db, BikingTrack, RunningTrack, MonthGoalDistance, TrackType, MonthGoalCount

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint(version: dict):
    api = Blueprint('api', __name__, static_folder='static', url_prefix='/api')

    @api.route('/version')
    @login_required
    def add():
        return jsonify(version)

    @api.route('/addBikingTrack', methods=['POST'])
    @login_required
    def addBikingTrack():
        try:
            form = BikingTrackFormModel.model_validate_json(request.data)
        except ValidationError as e:
            return jsonify({'error': str(e)}), 400

        track = BikingTrack(name=form.name,
                            startTime=form.calculate_start_time(),
                            duration=form.calculate_duration(),
                            distance=form.distance * 1000,
                            averageHeartRate=form.averageHeartRate,
                            elevationSum=form.elevationSum,
                            bike=form.bike,
                            user_id=current_user.id)

        LOGGER.debug(f'Saved new biking track from api: {track}')
        db.session.add(track)
        db.session.commit()

        return '', 200

    @api.route('/addRunningTrack', methods=['POST'])
    @login_required
    def addRunningTrack():
        try:
            form = RunningTrackFormModel.model_validate_json(request.data)
        except ValidationError as e:
            return jsonify({'error': str(e)}), 400

        track = RunningTrack(name=form.name,
                             startTime=form.calculate_start_time(),
                             duration=form.calculate_duration(),
                             distance=form.distance * 1000,
                             averageHeartRate=form.averageHeartRate,
                             elevationSum=form.elevationSum,
                             user_id=current_user.id)

        LOGGER.debug(f'Saved new running track api: {track}')
        db.session.add(track)
        db.session.commit()

        return '', 200

    @api.route('/addMonthGoalDistance', methods=['POST'])
    @login_required
    def addMonthGoalDistance():
        try:
            form = MonthGoalDistanceFormModel.model_validate_json(request.data)
        except ValidationError as e:
            return jsonify({'error': str(e)}), 400

        monthGoal = MonthGoalDistance(type=TrackType(form.type),
                                      year=form.year,
                                      month=form.month,
                                      distance_minimum=form.distance_minimum * 1000,
                                      distance_perfect=form.distance_perfect * 1000,
                                      user_id=current_user.id)

        LOGGER.debug(f'Saved new month goal of type "distance" from api: {monthGoal}')
        db.session.add(monthGoal)
        db.session.commit()

        return '', 200

    @api.route('/addMonthGoalCount', methods=['POST'])
    @login_required
    def addMonthGoalCount():
        try:
            form = MonthGoalCountFormModel.model_validate_json(request.data)
        except ValidationError as e:
            return jsonify({'error': str(e)}), 400

        monthGoal = MonthGoalCount(type=TrackType(form.type),
                                   year=form.year,
                                   month=form.month,
                                   count_minimum=form.count_minimum,
                                   count_perfect=form.count_perfect,
                                   user_id=current_user.id)
        LOGGER.debug(f'Saved new month goal of type "count" from api: {monthGoal}')
        db.session.add(monthGoal)
        db.session.commit()

        return '', 200

    return api
