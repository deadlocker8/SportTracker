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
from logic.model.Models import db, User

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

        currentDirectory = os.path.abspath(os.path.dirname(__file__))
        databasePath = os.path.join(os.path.dirname(currentDirectory), 'sportTracker.db')
        app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///' + databasePath

        db.init_app(app)

        with app.app_context():
            db.create_all()
            self.__create_users(db)

        @app.context_processor
        def inject_version_name() -> dict[str, Any]:
            return {'versionName': self._version['name']}

        return app

    def __create_users(self, database):
        for username in self._userService.get_users().keys():
            existingUser = User.query.filter_by(username=username).first()
            if existingUser is None:
                LOGGER.debug(f'Creating missing user "{username}"')
                user = User()
                user.username = username
                database.session.add(user)
                database.session.commit()

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
