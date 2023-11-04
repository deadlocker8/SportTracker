from dataclasses import dataclass
from datetime import datetime, date

from TheCodeLabs_BaseUtils.DefaultLogger import DefaultLogger
from TheCodeLabs_FlaskUtils.auth.SessionLoginWrapper import require_login
from flask import Blueprint, render_template, session, redirect, url_for
from flask_pydantic import validate
from pydantic import BaseModel

from logic import Constants
from logic.model.Models import Track, TrackType, db, User

LOGGER = DefaultLogger().create_logger_if_not_exists(Constants.APP_NAME)


class TrackFormModel(BaseModel):
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


def construct_blueprint():
    tracks = Blueprint('tracks', __name__, static_folder='static', url_prefix='/tracks')

    @tracks.route('/')
    @require_login
    def listTracks():
        tracks = Track.query.join(User).filter(User.username == session['username']).order_by(
            Track.startTime.desc()).all()

        tracksByMonth: list[MonthModel] = []
        currentMonth = None
        currentTracks = []
        for track in tracks:
            month = date(year=track.startTime.year, month=track.startTime.month, day=1)
            if month != currentMonth:
                if currentMonth is not None:
                    tracksByMonth.append(MonthModel(currentMonth.strftime('%B %Y'), currentTracks))
                currentMonth = date(year=track.startTime.year, month=track.startTime.month, day=1)
                currentTracks = []

            currentTracks.append(track)

        tracksByMonth.append(MonthModel(currentMonth.strftime('%B %Y'), currentTracks))

        return render_template('index.jinja2', tracksByMonth=tracksByMonth)

    @tracks.route('/add')
    @require_login
    def add():
        return render_template('trackAdd.jinja2')

    @tracks.route('/post', methods=['POST'])
    @require_login
    @validate()
    def addPost(form: TrackFormModel):
        duration = 3600 * form.durationHours + 60 * form.durationMinutes + form.durationSeconds

        track = Track(type=TrackType.BICYCLE,
                      name=form.name,
                      startTime=datetime.strptime(f'{form.date} {form.time}', '%Y-%m-%d %H:%M'),
                      duration=duration, distance=form.distance * 1000, user_id=session['userId'])
        LOGGER.debug(f'Saved new track: {track}')
        db.session.add(track)
        db.session.commit()

        return redirect(url_for('tracks.listTracks'))

    return tracks
