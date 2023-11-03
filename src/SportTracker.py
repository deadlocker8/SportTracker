import logging
import os
from typing import Any

import click
from TheCodeLabs_BaseUtils.DefaultLogger import DefaultLogger
from TheCodeLabs_FlaskUtils import FlaskBaseApp
from flask import Flask

from blueprints import General, Authentication
from logic import Constants
from logic.UserService import UserService

LOGGER = DefaultLogger().create_logger_if_not_exists(Constants.APP_NAME)


class SportTracker(FlaskBaseApp):
    def __init__(self, appName: str, rootDir: str, logger: logging.Logger, isDebug: bool = False):
        super().__init__(appName, rootDir, logger, serveFavicon=False)

        self._userService = UserService(self._settings['users'])
        self._isDebug = isDebug

        loggingSettings = self._settings['logging']
        if loggingSettings['enableRotatingLogFile']:
            DefaultLogger.add_rotating_file_handler(LOGGER,
                                                    fileName=loggingSettings['fileName'],
                                                    maxBytes=loggingSettings['maxBytes'],
                                                    backupCount=loggingSettings['numberOfBackups'])

    def _create_flask_app(self):
        app = Flask(self._rootDir)
        app.debug = self._isDebug

        @app.context_processor
        def inject_version_name() -> dict[str, Any]:
            return {'versionName': self._version['name']}

        return app

    def _register_blueprints(self, app):
        app.register_blueprint(Authentication.construct_blueprint(self._userService))
        app.register_blueprint(General.construct_blueprint())


@click.command()
@click.option('--debug', '-d', is_flag=True, help="Enable debug mode")
def start(debug):
    server = SportTracker(Constants.APP_NAME, os.path.dirname(__file__), LOGGER, debug)
    server.start_server()


if __name__ == '__main__':
    start()