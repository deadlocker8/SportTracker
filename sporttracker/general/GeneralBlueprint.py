import logging
import os

from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required

from sporttracker import Constants
from sporttracker.helpers.ChangelogParser import ChangelogParser

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint():
    general = Blueprint('general', __name__, static_folder='static')

    @general.route('/', methods=['GET'])
    @login_required
    def index():
        if current_user.isAdmin:
            return redirect(url_for('users.listUsers'))

        return redirect(url_for('workouts.listWorkouts'))

    @general.route('/about', methods=['GET'])
    @login_required
    def about():
        currentDirectory = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
        changelogPath = os.path.join(currentDirectory, 'CHANGES.md')
        return render_template('about.jinja2', releases=ChangelogParser(changelogPath).parse())

    @general.route('/icons', methods=['GET'])
    @login_required
    def icons():
        return render_template('icons.jinja2')

    @general.route('/api', methods=['GET'])
    @login_required
    def api():
        return redirect(url_for('api.docs'))

    return general
