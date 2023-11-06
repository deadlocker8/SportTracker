from TheCodeLabs_BaseUtils.DefaultLogger import DefaultLogger
from flask import Blueprint, redirect, url_for
from flask_login import login_required, current_user

from logic import Constants

LOGGER = DefaultLogger().create_logger_if_not_exists(Constants.APP_NAME)


def construct_blueprint():
    general = Blueprint('general', __name__, static_folder='static')

    @general.route('/')
    @login_required
    def index():
        if current_user.isAdmin:
            return redirect(url_for('users.listUsers'))

        return redirect(url_for('tracks.listTracks'))

    return general
