import logging
from dataclasses import dataclass
from datetime import datetime, date

from flask import Blueprint, render_template, redirect, url_for, abort
from flask_login import login_required, current_user
from flask_pydantic import validate
from pydantic import BaseModel, field_validator

from blueprints.MonthGoals import MonthGoalSummary, get_month_goal_summary
from logic import Constants
from logic.model.Models import Track, TrackType, db, User, MonthGoal

LOGGER = logging.getLogger(Constants.APP_NAME)


class TrackFormModel(BaseModel):
    type: str
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


@dataclass
class MonthModel:
    name: str
    tracks: list[Track]
    goals: list[MonthGoalSummary]


def construct_blueprint():
    tracks = Blueprint('tracks', __name__, static_folder='static', url_prefix='/tracks')

    @tracks.route('/')
    @login_required
    def listTracks():
        trackList = Track.query.join(User).filter(User.username == current_user.username).order_by(
            Track.startTime.desc()).all()

        tracksByMonth: list[MonthModel] = []
        currentMonth = None
        currentTracks = []
        for track in trackList:
            month = date(year=track.startTime.year, month=track.startTime.month, day=1)
            if month != currentMonth:
                if currentMonth is not None:
                    tracksByMonth.append(MonthModel(currentMonth.strftime('%B %Y'),
                                                    currentTracks,
                                                    __get_goal_summaries(currentMonth)))
                currentMonth = date(year=track.startTime.year, month=track.startTime.month, day=1)
                currentTracks = []

            currentTracks.append(track)

        if trackList:
            tracksByMonth.append(MonthModel(currentMonth.strftime('%B %Y'),
                                            currentTracks,
                                            __get_goal_summaries(currentMonth)))

        return render_template('tracks.jinja2', tracksByMonth=tracksByMonth)

    def __get_goal_summaries(dateObject: date) -> list[MonthGoalSummary]:
        goals = (MonthGoal.query.join(User)
                 .filter(User.username == current_user.username)
                 .filter(MonthGoal.year == dateObject.year)
                 .filter(MonthGoal.month == dateObject.month)
                 .all())

        if not goals:
            return []

        return [get_month_goal_summary(goal) for goal in goals]

    @tracks.route('/add')
    @login_required
    def add():
        return render_template('trackForm.jinja2')

    @tracks.route('/post', methods=['POST'])
    @login_required
    @validate()
    def addPost(form: TrackFormModel):
        duration = __calculate_duration(form)

        track = Track(type=TrackType(form.type),
                      name=form.name,
                      startTime=__calculate_start_time(form),
                      duration=duration,
                      distance=form.distance * 1000,
                      averageHeartRate=form.averageHeartRate,
                      elevationSum=form.elevationSum,
                      user_id=current_user.id)
        LOGGER.debug(f'Saved new track: {track}')
        db.session.add(track)
        db.session.commit()

        return redirect(url_for('tracks.listTracks'))

    @tracks.route('/edit/<int:track_id>')
    @login_required
    def edit(track_id: int):
        track = (Track.query.join(User)
                 .filter(User.username == current_user.username)
                 .filter(Track.id == track_id)
                 .first())

        if track is None:
            abort(404)

        trackModel = TrackFormModel(type=track.type.name,
                                    name=track.name,
                                    date=track.startTime.strftime('%Y-%m-%d'),
                                    time=track.startTime.strftime('%H:%M'),
                                    distance=track.distance / 1000,
                                    durationHours=track.duration // 3600,
                                    durationMinutes=track.duration % 3600 // 60,
                                    durationSeconds=track.duration % 3600 % 60,
                                    averageHeartRate=track.averageHeartRate,
                                    elevationSum=track.elevationSum)

        return render_template('trackForm.jinja2', track=trackModel, track_id=track_id)

    @tracks.route('/edit/<int:track_id>', methods=['POST'])
    @login_required
    @validate()
    def editPost(track_id: int, form: TrackFormModel):
        track = (Track.query.join(User)
                 .filter(User.username == current_user.username)
                 .filter(Track.id == track_id)
                 .first())

        if track is None:
            abort(404)

        duration = __calculate_duration(form)

        track.type = TrackType(form.type)
        track.name = form.name
        track.startTime = __calculate_start_time(form)
        track.distance = form.distance * 1000
        track.duration = duration
        track.averageHeartRate = form.averageHeartRate
        track.elevationSum = form.elevationSum
        track.user_id = current_user.id

        LOGGER.debug(f'Updated track: {track}')
        db.session.commit()

        return redirect(url_for('tracks.listTracks'))

    @tracks.route('/delete/<int:track_id>')
    @login_required
    def delete(track_id: int):
        track = (Track.query.join(User)
                 .filter(User.username == current_user.username)
                 .filter(Track.id == track_id)
                 .first())

        if track is None:
            abort(404)

        LOGGER.debug(f'Deleted track: {track}')
        db.session.delete(track)
        db.session.commit()

        return redirect(url_for('tracks.listTracks'))

    def __calculate_start_time(form):
        return datetime.strptime(f'{form.date} {form.time}', '%Y-%m-%d %H:%M')

    def __calculate_duration(form):
        return 3600 * form.durationHours + 60 * form.durationMinutes + form.durationSeconds

    return tracks
