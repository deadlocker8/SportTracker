import logging

from flask import Blueprint, render_template
from flask_login import login_required

from sporttracker.logic import Constants

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint():
    notifications = Blueprint('notifications', __name__, static_folder='static', url_prefix='/notifications')

    @notifications.route('/')
    @login_required
    def listNotifications():
        return render_template(
            'notifications/notifications.jinja2',
        )

    return notifications
