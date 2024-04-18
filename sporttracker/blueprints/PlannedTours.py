import logging
from dataclasses import dataclass
from datetime import datetime

from flask import Blueprint, render_template
from flask_login import login_required
from pydantic import BaseModel

from sporttracker.logic import Constants
from sporttracker.logic.QuickFilterState import get_quick_filter_state_from_session
from sporttracker.logic.model.Track import TrackType

LOGGER = logging.getLogger(Constants.APP_NAME)


@dataclass
class PlannedTourModel:
    id: int
    name: str
    lastEditDate: datetime
    type: TrackType


class PlannedTourFormModel(BaseModel):
    name: str
    type: str


def construct_blueprint():
    plannedTours = Blueprint(
        'plannedTours', __name__, static_folder='static', url_prefix='/plannedTours'
    )

    @plannedTours.route('/')
    @login_required
    def listPlannedTours():
        quickFilterState = get_quick_filter_state_from_session()

        return render_template(
            'plannedTours/plannedTours.jinja2',
            plannedTours=[],
            quickFilterState=quickFilterState,
        )

    return plannedTours
