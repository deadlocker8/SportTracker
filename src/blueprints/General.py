from TheCodeLabs_BaseUtils.DefaultLogger import DefaultLogger
from TheCodeLabs_FlaskUtils.auth.SessionLoginWrapper import require_login
from flask import Blueprint, render_template, session

from logic import Constants
from logic.model.Models import Track, User

LOGGER = DefaultLogger().create_logger_if_not_exists(Constants.APP_NAME)


def construct_blueprint():
    general = Blueprint('general', __name__, static_folder='static')

    @general.route('/')
    @require_login
    def index():
        tracks = Track.query.join(User).filter(User.username == session['username']).order_by(Track.startTime.desc()).all()
        return render_template('index.jinja2', tracks=tracks)

    return general
