import logging
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, abort, jsonify
from flask_login import login_required, current_user
from flask_pydantic import validate
from pydantic import BaseModel, field_validator

from logic import Constants
from logic.model.Models import db, User, BikingTrack

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint(version: dict):
    api = Blueprint('api', __name__, static_folder='static', url_prefix='/api')

    @api.route('/version')
    @login_required
    def add():
        return jsonify(version)

    return api
