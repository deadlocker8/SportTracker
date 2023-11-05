from dataclasses import dataclass
from datetime import datetime, date

from TheCodeLabs_BaseUtils.DefaultLogger import DefaultLogger
from TheCodeLabs_FlaskUtils.auth.SessionLoginWrapper import require_login
from flask import Blueprint, render_template, session, redirect, url_for, abort
from flask_pydantic import validate
from pydantic import BaseModel

from blueprints.MonthGoals import MonthGoalSummary, get_month_goal_summary
from logic import Constants
from logic.model.Models import Track, TrackType, db, User, MonthGoal

LOGGER = DefaultLogger().create_logger_if_not_exists(Constants.APP_NAME)


class TrackFormModel(BaseModel):
    type: str
    name: str
    date: str
    time: str
    distance: float
    durationHours: int
    durationMinutes: int
    durationSeconds: int


@dataclass
class MonthModel:
    name: str
    tracks: list[Track]
    goals: list[MonthGoalSummary]


def construct_blueprint():
    tracks = Blueprint('tracks', __name__, static_folder='static', url_prefix='/tracks')

    @tracks.route('/')
    @require_login
    def listTracks():
        trackList = Track.query.join(User).filter(User.username == session['username']).order_by(
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
                 .filter(User.username == session['username'])
                 .filter(MonthGoal.year == dateObject.year)
                 .filter(MonthGoal.month == dateObject.month)
                 .all())

        if not goals:
            return []

        return [get_month_goal_summary(goal) for goal in goals]

    @tracks.route('/add')
    @require_login
    def add():
        return render_template('trackForm.jinja2')

    @tracks.route('/post', methods=['POST'])
    @require_login
    @validate()
    def addPost(form: TrackFormModel):
        duration = __calculate_duration(form)

        track = Track(type=TrackType(form.type),
                      name=form.name,
                      startTime=__calculate_start_time(form),
                      duration=duration, distance=form.distance * 1000, user_id=session['userId'])
        LOGGER.debug(f'Saved new track: {track}')
        db.session.add(track)
        db.session.commit()

        return redirect(url_for('tracks.listTracks'))

    @tracks.route('/edit/<int:track_id>')
    @require_login
    def edit(track_id: int):
        track = (Track.query.join(User)
                 .filter(User.username == session['username'])
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
                                    durationSeconds=track.duration % 3600 % 60)

        return render_template('trackForm.jinja2', track=trackModel, track_id=track_id)

    @tracks.route('/edit/<int:track_id>', methods=['POST'])
    @require_login
    @validate()
    def editPost(track_id: int, form: TrackFormModel):
        track = (Track.query.join(User)
                 .filter(User.username == session['username'])
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
        track.user_id = session['userId']

        LOGGER.debug(f'Updated track: {track}')
        db.session.commit()

        return redirect(url_for('tracks.listTracks'))

    @tracks.route('/delete/<int:track_id>')
    @require_login
    def delete(track_id: int):
        track = (Track.query.join(User)
                 .filter(User.username == session['username'])
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
        duration = 3600 * form.durationHours + 60 * form.durationMinutes + form.durationSeconds
        return duration

    return tracks
