import logging

from flask import Blueprint, render_template
from flask_login import fresh_login_required

from sporttracker import Constants
from sporttracker.authentication.AdminWrapper import admin_role_required
from sporttracker.metrics.LoadStatisticsCollector import LoadStatisticsCollector
from sporttracker.serverStatistics.ServerStatisticsService import ServerStatisticsService

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint(dataFolderPath: str, loadStatisticsCollector: LoadStatisticsCollector):
    serverStatistics = Blueprint('serverStatistics', __name__, static_folder='static', url_prefix='/serverStatistics')

    service = ServerStatisticsService(dataFolderPath, loadStatisticsCollector)

    @serverStatistics.route('/', methods=['GET'])
    @admin_role_required
    @fresh_login_required
    def listServerStatistics():
        return render_template(
            'serverStatistics/serverStatistics.jinja2',
            globalStatistics=service.get_global_statistics(),
            userStatistics=service.get_user_statistics(),
            cacheCalculationStatistics=service.get_cache_calculation_statistics(),
        )

    return serverStatistics
