import logging

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from pydantic import ValidationError

from blueprints.BikingTracks import BikingTrackFormModel
from blueprints.RunningTracks import RunningTrackFormModel
from logic import Constants
from logic.model.Models import db, BikingTrack, RunningTrack

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

        duration = form.calculate_duration()

        track = BikingTrack(name=form.name,
                            startTime=form.calculate_start_time(),
                            duration=duration,
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

        duration = form.calculate_duration()

        track = RunningTrack(name=form.name,
                             startTime=form.calculate_start_time(),
                             duration=duration,
                             distance=form.distance * 1000,
                             averageHeartRate=form.averageHeartRate,
                             elevationSum=form.elevationSum,
                             user_id=current_user.id)

        LOGGER.debug(f'Saved new running track api: {track}')
        db.session.add(track)
        db.session.commit()

        return '', 200

    return api
