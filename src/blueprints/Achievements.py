import logging

from flask import Blueprint, render_template
from flask_login import login_required

from logic import Constants

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint():
    achievements = Blueprint('achievements', __name__, static_folder='static', url_prefix='/achievements')

    @achievements.route('/')
    @login_required
    def showAchievements():
        return render_template('achievements.jinja2')

    return achievements
