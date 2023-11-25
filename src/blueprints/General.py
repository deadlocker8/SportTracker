import logging
import os
from collections import OrderedDict

from flask import Blueprint, redirect, url_for, render_template
from flask_login import login_required, current_user

from logic import Constants

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint():
    general = Blueprint('general', __name__, static_folder='static')

    @general.route('/')
    @login_required
    def index():
        if current_user.isAdmin:
            return redirect(url_for('users.listUsers'))

        return redirect(url_for('tracks.listTracks'))

    @general.route('/about')
    @login_required
    def about():
        currentDirectory = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
        changelogPath = os.path.join(currentDirectory, 'CHANGES.md')
        with open(changelogPath, encoding='utf-8') as f:
            lines = f.readlines()

        changelog = OrderedDict()
        currentList = []
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue

            if line.startswith('#'):
                changelog[line[2:]] = currentList
                currentList = []
            if line.startswith('-'):
                currentList.append(line[2:])

        return render_template('about.jinja2', changelog=OrderedDict(reversed(list(changelog.items()))))

    return general
