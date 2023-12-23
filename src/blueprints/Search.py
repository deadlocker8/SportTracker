import logging

from flask import Blueprint, render_template
from flask_login import login_required

from logic import Constants

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint():
    search = Blueprint('search', __name__, static_folder='static', url_prefix='/search')

    @search.route('/search', methods=['POST'])
    @login_required
    def performSearch():
        return render_template('search.jinja2', results=[])

    return search
