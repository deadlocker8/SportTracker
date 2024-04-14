import logging
from dataclasses import dataclass
from datetime import datetime

from flask import Blueprint, render_template
from flask_login import login_required, current_user

from sporttracker.logic import Constants
from sporttracker.logic.model.MaintenanceEvent import MaintenanceEvent
from sporttracker.logic.model.Track import TrackType

LOGGER = logging.getLogger(Constants.APP_NAME)


@dataclass
class MaintenanceEventModel:
    id: int
    eventDate: datetime
    type: TrackType
    description: str


def construct_blueprint():
    maintenanceEvents = Blueprint('maintenanceEvents', __name__, static_folder='static',
                                  url_prefix='/maintenanceEvents')

    @maintenanceEvents.route('/')
    @login_required
    def listMaintenanceEvents():
        events: list[MaintenanceEvent] = (
            MaintenanceEvent.query
            .filter(MaintenanceEvent.user_id == current_user.id)
            .all())

        maintenanceEventList = []
        for event in events:
            maintenanceEventList.append(MaintenanceEventModel(event.id, event.event_date, event.type, event.description))

        return render_template('maintenanceEvents/maintenanceEvents.jinja2',
                               maintenanceEvents=maintenanceEventList)

    return maintenanceEvents
