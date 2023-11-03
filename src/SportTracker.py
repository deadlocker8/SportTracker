import logging
import os

from TheCodeLabs_BaseUtils.DefaultLogger import DefaultLogger
from TheCodeLabs_FlaskUtils import FlaskBaseApp

from blueprints import General, Authentication
from logic import Constants
from logic.UserService import UserService

LOGGER = DefaultLogger().create_logger_if_not_exists(Constants.APP_NAME)


class SportTracker(FlaskBaseApp):
    def __init__(self, appName: str, rootDir: str, logger: logging.Logger):
        super().__init__(appName, rootDir, logger, serveFavicon=False)

        self._userService = UserService(self._settings['users'])

        loggingSettings = self._settings['logging']
        if loggingSettings['enableRotatingLogFile']:
            DefaultLogger.add_rotating_file_handler(LOGGER,
                                                    fileName=loggingSettings['fileName'],
                                                    maxBytes=loggingSettings['maxBytes'],
                                                    backupCount=loggingSettings['numberOfBackups'])

    def _register_blueprints(self, app):
        versionName = self._version['name']
        app.register_blueprint(Authentication.construct_blueprint(versionName, self._userService))
        app.register_blueprint(General.construct_blueprint(versionName))


if __name__ == '__main__':
    server = SportTracker(Constants.APP_NAME, os.path.dirname(__file__), LOGGER)
    server.start_server()
