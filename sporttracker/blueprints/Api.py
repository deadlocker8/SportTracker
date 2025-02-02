import logging

from flask import Blueprint, jsonify, render_template, redirect, url_for
from flask_login import login_required

from sporttracker.logic import Constants

LOGGER = logging.getLogger(Constants.APP_NAME)

API_VERSION = '2.0.0'


def construct_blueprint(version: dict):
    api = Blueprint('api', __name__, static_folder='static', url_prefix='/api')

    @api.route('/')
    @login_required
    def apiIndex():
        return redirect(url_for('api.docs'))

    @api.route('/version')
    @login_required
    def getVersion():
        return jsonify({'version': API_VERSION})

    @api.route('/docs')
    @login_required
    def docs():
        return render_template('swaggerui/swaggerui.jinja2')

    return api
