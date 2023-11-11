import logging
import os
import secrets
import string
from datetime import datetime
from typing import Any

import click
from TheCodeLabs_BaseUtils.DefaultLogger import DefaultLogger
from TheCodeLabs_FlaskUtils import FlaskBaseApp
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

from blueprints import General, Authentication, Tracks, MonthGoals, Charts, Users, BikingTracks, RunningTracks
from logic import Constants
from logic.model.Models import db, User, Track, TrackType, MonthGoal, get_number_of_all_tracks

LOGGER = DefaultLogger().create_logger_if_not_exists(Constants.APP_NAME)


class SportTracker(FlaskBaseApp):
    def __init__(self, appName: str, rootDir: str, logger: logging.Logger, isDebug: bool, generateDummyData: bool):
        super().__init__(appName, rootDir, logger, serveFavicon=False)

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
            self.__create_admin_user(db)

            if self._generateDummyData:
                self.__create_dummy_data(db)

        @app.context_processor
        def inject_version_name() -> dict[str, Any]:
            return {'versionName': self._version['name']}

        def format_duration(value: int | None) -> str:
            if value is None:
                return '--:--'

            hours = value // 3600
            minutes = value % 3600 // 60

            return f'{hours}:{str(minutes).zfill(2)}'

        def format_actual_distance(value: float) -> str:
            value = str(int(value))

            if len(value) == 1:
                return f'&nbsp;&nbsp;{value}'
            elif len(value) == 2:
                return f'&nbsp;{value}'
            else:
                return value

        def format_pace(track: Track) -> str:
            speed = int(track.duration / (track.distance / 1000))

            minutes = speed // 60
            seconds = speed % 60
            return f'{minutes}:{str(seconds).zfill(2)}'

        app.add_template_filter(format_duration)
        app.add_template_filter(format_actual_distance)
        app.add_template_filter(format_pace)

        login_manager = LoginManager()
        login_manager.login_view = 'authentication.login'
        login_manager.init_app(app)

        @login_manager.user_loader
        def load_user(user_id):
            return User.query.get(int(user_id))

        return app

    def __create_admin_user(self, database):
        if User.query.filter_by(username='admin').first() is None:
            LOGGER.debug(f'Creating admin user')
            password = self.__generate_password()
            LOGGER.info(f'Created default admin user with password: "{password}". CAUTION: password is only shown once. Save it now!')

            user = User(username='admin', password=Bcrypt().generate_password_hash(password).decode('utf-8'), isAdmin=True)
            database.session.add(user)
            database.session.commit()

    def __generate_password(self) -> str:
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for i in range(20))

    def __create_dummy_data(self, database):
        user = User.query.filter_by(username='demo').first()
        if user is None:
            LOGGER.debug(f'Creating demo user')
            user = User(username='demo', password=Bcrypt().generate_password_hash('demo').decode('utf-8'), isAdmin=False)
            database.session.add(user)

        if Track.query.count() == 0:
            LOGGER.debug('Creating dummy data...')

            track = Track(type=TrackType.BICYCLE,
                          name='Short after work',
                          startTime=datetime(year=2023, month=11, day=3, hour=12, minute=15, second=48),
                          duration=60 * 35, distance=1000 * 15, averageHeartRate=88, elevationSum=512, user_id=user.id)
            database.session.add(track)
            track = Track(type=TrackType.BICYCLE,
                          name='Normal One',
                          startTime=datetime(year=2023, month=10, day=15, hour=18, minute=23, second=12),
                          duration=60 * 67, distance=1000 * 31, averageHeartRate=122, elevationSum=16, user_id=user.id)
            database.session.add(track)
            track = Track(type=TrackType.BICYCLE,
                          name='Longest tour I\'ve ever made and was quite interesting',
                          startTime=datetime(year=2023, month=10, day=28, hour=19, minute=30, second=41),
                          duration=60 * 93, distance=1000 * 42.2, averageHeartRate=165, elevationSum=138, user_id=user.id)
            database.session.add(track)

            monthGoal = MonthGoal(type=TrackType.BICYCLE, year=2023, month=11, distance_minimum=100 * 1000,
                                  distance_perfect=200 * 1000, user_id=user.id)
            database.session.add(monthGoal)
            monthGoal = MonthGoal(type=TrackType.BICYCLE, year=2023, month=9, distance_minimum=100 * 1000,
                                  distance_perfect=200 * 1000, user_id=user.id)
            database.session.add(monthGoal)
            monthGoal = MonthGoal(type=TrackType.BICYCLE, year=2023, month=10, distance_minimum=50 * 1000,
                                  distance_perfect=100 * 1000, user_id=user.id)
            database.session.add(monthGoal)
            database.session.commit()

    def _register_blueprints(self, app):
        app.register_blueprint(Authentication.construct_blueprint())
        app.register_blueprint(General.construct_blueprint())
        app.register_blueprint(Tracks.construct_blueprint())
        app.register_blueprint(BikingTracks.construct_blueprint())
        app.register_blueprint(RunningTracks.construct_blueprint())
        app.register_blueprint(MonthGoals.construct_blueprint())
        app.register_blueprint(Charts.construct_blueprint())
        app.register_blueprint(Users.construct_blueprint())


@click.command()
@click.option('--debug', '-d', is_flag=True, help="Enable debug mode")
@click.option('--dummy', '-dummy', is_flag=True, help="Generate dummy tracks")
def start(debug, dummy):
    server = SportTracker(Constants.APP_NAME, os.path.dirname(__file__), LOGGER, debug, dummy)
    server.start_server()


if __name__ == '__main__':
    start()
