import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from flask import Blueprint, render_template
from flask_login import login_required

from sporttracker.logic import Constants
from sporttracker.logic.model.Track import TrackType

LOGGER = logging.getLogger(Constants.APP_NAME)


@dataclass
class MaintenanceEventModel:
    eventDate: datetime
    type: TrackType
    description: str


def construct_blueprint():
    maintenanceEvents = Blueprint('maintenanceEvents', __name__, static_folder='static',
                                  url_prefix='/maintenanceEvents')

    @maintenanceEvents.route('/')
    @login_required
    def listMaintenanceEvents():
        maintenanceEvents = [
            MaintenanceEventModel(datetime.now(), TrackType.BIKING, 'chain oiled'),
            MaintenanceEventModel(datetime.now() - timedelta(days=7), TrackType.BIKING, 'New break pads'),
            MaintenanceEventModel(datetime.now() - timedelta(days=10), TrackType.BIKING, 'chain oiled'),
        ]
        return render_template('maintenanceEvents/maintenanceEvents.jinja2',
                               maintenanceEvents=maintenanceEvents)

    return maintenanceEvents
