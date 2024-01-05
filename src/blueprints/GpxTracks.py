import logging

from flask import Blueprint

from logic import Constants

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint():
    gpxTracks = Blueprint('gpxTracks', __name__, static_folder='static')

    return gpxTracks
