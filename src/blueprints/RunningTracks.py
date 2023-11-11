import logging
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, abort
from flask_login import login_required, current_user
from flask_pydantic import validate
from pydantic import BaseModel, field_validator

from logic import Constants
from logic.model.Models import db, User, RunningTrack

LOGGER = logging.getLogger(Constants.APP_NAME)


class RunningTrackFormModel(BaseModel):
    name: str
    date: str
    time: str
    distance: float
    durationHours: int
    durationMinutes: int
    durationSeconds: int
    averageHeartRate: int | None = None
    elevationSum: int | None = None

    @field_validator(*['averageHeartRate', 'elevationSum'], mode='before')
    def averageHeartRateCheck(cls, value: str, info) -> str | None:
        if isinstance(value, str):
            value = value.strip()
        if value == '':
            return None
        return value


def construct_blueprint():
    runningTracks = Blueprint('runningTracks', __name__, static_folder='static', url_prefix='/runningTracks')

    @runningTracks.route('/add')
    @login_required
    def add():
        return render_template('trackRunningForm.jinja2')

    @runningTracks.route('/post', methods=['POST'])
    @login_required
    @validate()
    def addPost(form: RunningTrackFormModel):
        duration = __calculate_duration(form)

        track = RunningTrack(name=form.name,
                             startTime=__calculate_start_time(form),
                             duration=duration,
                             distance=form.distance * 1000,
                             averageHeartRate=form.averageHeartRate,
                             elevationSum=form.elevationSum,
                             user_id=current_user.id)
        LOGGER.debug(f'Saved new running track: {track}')
        db.session.add(track)
        db.session.commit()

        return redirect(url_for('tracks.listTracks'))

    @runningTracks.route('/edit/<int:track_id>')
    @login_required
    def edit(track_id: int):
        track: RunningTrack | None = (RunningTrack.query.join(User)
                                      .filter(User.username == current_user.username)
                                      .filter(RunningTrack.id == track_id)
                                      .first())

        if track is None:
            abort(404)

        trackModel = RunningTrackFormModel(
            name=track.name,
            date=track.startTime.strftime('%Y-%m-%d'),
            time=track.startTime.strftime('%H:%M'),
            distance=track.distance / 1000,
            durationHours=track.duration // 3600,
            durationMinutes=track.duration % 3600 // 60,
            durationSeconds=track.duration % 3600 % 60,
            averageHeartRate=track.averageHeartRate,
            elevationSum=track.elevationSum)

        return render_template('trackRunningForm.jinja2', track=trackModel, track_id=track_id)

    @runningTracks.route('/edit/<int:track_id>', methods=['POST'])
    @login_required
    @validate()
    def editPost(track_id: int, form: RunningTrackFormModel):
        track = (RunningTrack.query.join(User)
                 .filter(User.username == current_user.username)
                 .filter(RunningTrack.id == track_id)
                 .first())

        if track is None:
            abort(404)

        duration = __calculate_duration(form)

        track.name = form.name
        track.startTime = __calculate_start_time(form)
        track.distance = form.distance * 1000
        track.duration = duration
        track.averageHeartRate = form.averageHeartRate
        track.elevationSum = form.elevationSum
        track.user_id = current_user.id

        LOGGER.debug(f'Updated running track: {track}')
        db.session.commit()

        return redirect(url_for('tracks.listTracks'))

    @runningTracks.route('/delete/<int:track_id>')
    @login_required
    def delete(track_id: int):
        track = (RunningTrack.query.join(User)
                 .filter(User.username == current_user.username)
                 .filter(RunningTrack.id == track_id)
                 .first())

        if track is None:
            abort(404)

        LOGGER.debug(f'Deleted running track: {track}')
        db.session.delete(track)
        db.session.commit()

        return redirect(url_for('tracks.listTracks'))

    def __calculate_start_time(form: RunningTrackFormModel) -> datetime:
        return datetime.strptime(f'{form.date} {form.time}', '%Y-%m-%d %H:%M')

    def __calculate_duration(form: RunningTrackFormModel) -> int:
        return 3600 * form.durationHours + 60 * form.durationMinutes + form.durationSeconds

    return runningTracks
