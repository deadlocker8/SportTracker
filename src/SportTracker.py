import logging
import os

from TheCodeLabs_BaseUtils.DefaultLogger import DefaultLogger
from TheCodeLabs_FlaskUtils import FlaskBaseApp

from blueprints import General
from logic import Constants

LOGGER = DefaultLogger().create_logger_if_not_exists(Constants.APP_NAME)


class SportTracker(FlaskBaseApp):
    def __init__(self, appName: str, rootDir: str, logger: logging.Logger):
        super().__init__(appName, rootDir, logger, serveFavicon=False)

        loggingSettings = self._settings['logging']
        if loggingSettings['enableRotatingLogFile']:
            DefaultLogger.add_rotating_file_handler(LOGGER,
                                                    fileName=loggingSettings['fileName'],
                                                    maxBytes=loggingSettings['maxBytes'],
                                                    backupCount=loggingSettings['numberOfBackups'])

    def _register_blueprints(self, app):
        app.register_blueprint(General.construct_blueprint())


if __name__ == '__main__':
    server = SportTracker(Constants.APP_NAME, os.path.dirname(__file__), LOGGER)
    server.start_server()
