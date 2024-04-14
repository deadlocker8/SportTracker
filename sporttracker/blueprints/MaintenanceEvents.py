import logging

from flask import Blueprint, render_template
from flask_login import login_required

from sporttracker.logic import Constants

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint():
    maintenanceEvents = Blueprint('maintenanceEvents', __name__, static_folder='static', url_prefix='/maintenanceEvents')

    @maintenanceEvents.route('/')
    @login_required
    def listMaintenanceEvents():
        return render_template('maintenanceEvents/maintenanceEvents.jinja2')

    return maintenanceEvents
