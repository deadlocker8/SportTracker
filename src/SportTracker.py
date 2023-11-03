import logging
import os
from datetime import datetime
from typing import Any

import click
from TheCodeLabs_BaseUtils.DefaultLogger import DefaultLogger
from TheCodeLabs_FlaskUtils import FlaskBaseApp
from flask import Flask

from blueprints import General, Authentication
from logic import Constants
from logic.UserService import UserService
from logic.model.Models import db, User, Track, TrackType

LOGGER = DefaultLogger().create_logger_if_not_exists(Constants.APP_NAME)


class SportTracker(FlaskBaseApp):
    def __init__(self, appName: str, rootDir: str, logger: logging.Logger, isDebug: bool, generateDummyData: bool):
        super().__init__(appName, rootDir, logger, serveFavicon=False)

        self._userService = UserService(self._settings['users'])
        self._isDebug = isDebug
        self._generateDummyData = generateDummyData

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

            if self._generateDummyData:
                self.__create_dummy_data(db)

        @app.context_processor
        def inject_version_name() -> dict[str, Any]:
            return {'versionName': self._version['name']}

        def format_duration(value):
            hours = value // 3600
            minutes = value % 3600 // 60

            return f'{hours}:{str(minutes).zfill(2)}'

        app.add_template_filter(format_duration)

        return app

    def __create_users(self, database):
        for username in self._userService.get_users().keys():
            existingUser = User.query.filter_by(username=username).first()
            if existingUser is None:
                LOGGER.debug(f'Creating missing user "{username}"')
                user = User(username=username)
                database.session.add(user)
                database.session.commit()

    def __create_dummy_data(self, database):
        if Track.query.count() == 0:
            LOGGER.debug('Creating dummy data...')

            track = Track(type=TrackType.BICYCLE,
                          name='Short after work',
                          startTime=datetime(year=2023, month=11, day=3, hour=12, minute=15, second=48),
                          duration=60 * 35, distance=1000 * 15, user_id=1)
            database.session.add(track)
            track = Track(type=TrackType.BICYCLE,
                          name='Normal One',
                          startTime=datetime(year=2023, month=10, day=15, hour=18, minute=23, second=12),
                          duration=60 * 67, distance=1000 * 31, user_id=1)
            database.session.add(track)
            track = Track(type=TrackType.BICYCLE,
                          name='Longest tour I\'ve ever made and was quite interesting',
                          startTime=datetime(year=2023, month=10, day=28, hour=19, minute=30, second=41),
                          duration=60 * 93, distance=1000 * 42.2, user_id=1)
            database.session.add(track)
            database.session.commit()

    def _register_blueprints(self, app):
        app.register_blueprint(Authentication.construct_blueprint(self._userService))
        app.register_blueprint(General.construct_blueprint())


@click.command()
@click.option('--debug', '-d', is_flag=True, help="Enable debug mode")
@click.option('--dummy', '-dummy', is_flag=True, help="Generate dummy tracks")
def start(debug, dummy):
    server = SportTracker(Constants.APP_NAME, os.path.dirname(__file__), LOGGER, debug, dummy)
    server.start_server()


if __name__ == '__main__':
    start()
