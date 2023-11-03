from TheCodeLabs_BaseUtils.DefaultLogger import DefaultLogger
from flask import Blueprint, render_template

from logic import Constants

LOGGER = DefaultLogger().create_logger_if_not_exists(Constants.APP_NAME)


def construct_blueprint(versionName: str):
    general = Blueprint('general', __name__, static_folder='static')

    @general.route('/')
    def index():
        return render_template('index.jinja2', versionName=versionName)

    return general
