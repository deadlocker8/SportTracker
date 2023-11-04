from datetime import datetime

from TheCodeLabs_BaseUtils.DefaultLogger import DefaultLogger
from TheCodeLabs_FlaskUtils.auth.SessionLoginWrapper import require_login
from flask import Blueprint, render_template, session, redirect, url_for
from flask_pydantic import validate
from pydantic import BaseModel

from logic import Constants
from logic.model.Models import Track, TrackType, db

LOGGER = DefaultLogger().create_logger_if_not_exists(Constants.APP_NAME)


class TrackFormModel(BaseModel):
    name: str
    date: str
    time: str
    distance: float
    durationHours: int
    durationMinutes: int
    durationSeconds: int


def construct_blueprint():
    tracks = Blueprint('tracks', __name__, static_folder='static', url_prefix='/tracks')

    @tracks.route('/add')
    @require_login
    def add():
        return render_template('trackAdd.jinja2')

    @tracks.route('/post', methods=['POST'])
    @require_login
    @validate()
    def addPost(form: TrackFormModel):
        duration = 3600 * form.durationHours + 60* form.durationMinutes + form.durationSeconds

        track = Track(type=TrackType.BICYCLE,
                      name=form.name,
                      startTime=datetime.strptime(f'{form.date} {form.time}', '%Y-%m-%d %H:%M'),
                      duration=duration, distance=form.distance * 1000, user_id=session['userId'])
        LOGGER.debug(f'Saved new track: {track}')
        db.session.add(track)
        db.session.commit()

        return redirect(url_for('general.index'))

    return tracks
