import logging
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from pydantic import ValidationError, BaseModel

from blueprints.MonthGoalsCount import MonthGoalCountFormModel
from blueprints.MonthGoalsDistance import MonthGoalDistanceFormModel
from logic import Constants
from logic.model.MonthGoal import MonthGoalDistance, MonthGoalCount
from logic.model.Track import Track, TrackType
from logic.model.db import db

LOGGER = logging.getLogger(Constants.APP_NAME)


class TrackApiFormModel(BaseModel):
    name: str
    type: str
    date: str
    time: str
    distance: float
    durationHours: int | None = None
    durationMinutes: int | None = None
    durationSeconds: int | None = None
    averageHeartRate: int | None = None
    elevationSum: int | None = None
    customFields: dict[str, str] | None = None

    def calculate_start_time(self) -> datetime:
        return datetime.strptime(f'{self.date} {self.time}', '%Y-%m-%d %H:%M')

    def calculate_duration(self) -> int | None:
        if self.durationHours is None:
            return None
        if self.durationMinutes is None:
            return None
        if self.durationSeconds is None:
            return None
        return 3600 * self.durationHours + 60 * self.durationMinutes + self.durationSeconds


def construct_blueprint(version: dict):
    api = Blueprint('api', __name__, static_folder='static', url_prefix='/api')

    @api.route('/version')
    @login_required
    def version():
        return jsonify(version)

    @api.route('/addTrack', methods=['POST'])
    @login_required
    def addTrack():
        try:
            form = TrackApiFormModel.model_validate_json(request.data)
        except ValidationError as e:
            return jsonify({'error': str(e)}), 400

        track = Track(
            name=form.name,
            type=TrackType(form.type),
            startTime=form.calculate_start_time(),
            duration=form.calculate_duration(),
            distance=form.distance * 1000,
            averageHeartRate=form.averageHeartRate,
            elevationSum=form.elevationSum,
            user_id=current_user.id,
            custom_fields={} if form.customFields is None else form.customFields,
        )

        LOGGER.debug(f'Saved new track of type {track.type} from api: {track}')
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

        monthGoal = MonthGoalDistance(
            type=TrackType(form.type),
            year=form.year,
            month=form.month,
            distance_minimum=form.distance_minimum * 1000,
            distance_perfect=form.distance_perfect * 1000,
            user_id=current_user.id,
        )

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

        monthGoal = MonthGoalCount(
            type=TrackType(form.type),
            year=form.year,
            month=form.month,
            count_minimum=form.count_minimum,
            count_perfect=form.count_perfect,
            user_id=current_user.id,
        )
        LOGGER.debug(f'Saved new month goal of type "count" from api: {monthGoal}')
        db.session.add(monthGoal)
        db.session.commit()

        return '', 200

    return api
