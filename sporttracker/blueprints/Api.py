import logging
from dataclasses import dataclass
from datetime import datetime

from flask import Blueprint, jsonify, request, abort
from flask_login import login_required, current_user
from pydantic import ValidationError, BaseModel

from sporttracker.blueprints.GpxTracks import handleGpxTrack
from sporttracker.blueprints.MonthGoalsCount import MonthGoalCountFormModel
from sporttracker.blueprints.MonthGoalsDistance import MonthGoalDistanceFormModel
from sporttracker.logic import Constants
from sporttracker.logic.model.MonthGoal import MonthGoalDistance, MonthGoalCount
from sporttracker.logic.model.Track import Track, TrackType
from sporttracker.logic.model.User import User
from sporttracker.logic.model.db import db

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


@dataclass
class TrackModel:
    id: int
    name: str
    type: str
    startTime: str
    distance: int
    duration: int | None = None
    averageHeartRate: int | None = None
    elevationSum: int | None = None
    gpxFileName: str | None = None
    customFields: dict[str, str] | None = None


def construct_blueprint(version: dict, uploadFolder: str):
    api = Blueprint('api', __name__, static_folder='static', url_prefix='/api')

    @api.route('/version')
    @login_required
    def getVersion():
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
            type=TrackType(form.type),  # type: ignore[call-arg]
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

        return {'id': track.id}, 200

    @api.route('/addMonthGoalDistance', methods=['POST'])
    @login_required
    def addMonthGoalDistance():
        try:
            form = MonthGoalDistanceFormModel.model_validate_json(request.data)
        except ValidationError as e:
            return jsonify({'error': str(e)}), 400

        monthGoal = MonthGoalDistance(
            type=TrackType(form.type),  # type: ignore[call-arg]
            year=form.year,
            month=form.month,
            distance_minimum=form.distance_minimum * 1000,
            distance_perfect=form.distance_perfect * 1000,
            user_id=current_user.id,
        )

        LOGGER.debug(f'Saved new month goal of type "distance" from api: {monthGoal}')
        db.session.add(monthGoal)
        db.session.commit()

        return {'id': monthGoal.id}, 200

    @api.route('/addMonthGoalCount', methods=['POST'])
    @login_required
    def addMonthGoalCount():
        try:
            form = MonthGoalCountFormModel.model_validate_json(request.data)
        except ValidationError as e:
            return jsonify({'error': str(e)}), 400

        monthGoal = MonthGoalCount(
            type=TrackType(form.type),  # type: ignore[call-arg]
            year=form.year,
            month=form.month,
            count_minimum=form.count_minimum,
            count_perfect=form.count_perfect,
            user_id=current_user.id,
        )
        LOGGER.debug(f'Saved new month goal of type "count" from api: {monthGoal}')
        db.session.add(monthGoal)
        db.session.commit()

        return {'id': monthGoal.id}, 200

    @api.route('/addGpxTrack/<int:track_id>', methods=['POST'])
    @login_required
    def addGpxTrackTrack(track_id: int):
        track = (
            Track.query.join(User)
            .filter(User.username == current_user.username)
            .filter(Track.id == track_id)
            .first()
        )

        if track is None:
            abort(404)

        newGpxFileName = handleGpxTrack(request.files, uploadFolder)
        if newGpxFileName is None:
            abort(400)

        track.gpxFileName = newGpxFileName

        LOGGER.debug(f'Added gpx track {newGpxFileName} to track {track.id}')
        db.session.add(track)
        db.session.commit()

        return '', 200

    @api.route('/tracks')
    @login_required
    def getTracks():
        tracks = (
            Track.query.join(User)
            .filter(User.username == current_user.username)
            .order_by(Track.startTime.desc())
            .all()
        )

        result = []
        for track in tracks:
            result.append(
                TrackModel(
                    id=track.id,
                    name=track.name,
                    type=track.type.name,
                    startTime=track.startTime.strftime('%Y-%m-%d %H:%M:%S'),
                    distance=track.distance,
                    duration=track.duration,
                    averageHeartRate=track.averageHeartRate,
                    elevationSum=track.elevationSum,
                    gpxFileName=track.gpxFileName,
                    customFields=track.custom_fields,
                )
            )

        return result, 200

    return api
