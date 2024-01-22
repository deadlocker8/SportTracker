import logging
import os
import secrets
import string
from typing import Any

import click
from TheCodeLabs_BaseUtils.DefaultLogger import DefaultLogger
from TheCodeLabs_FlaskUtils import FlaskBaseApp
from flask import Flask, request
from flask_babel import Babel
from flask_login import LoginManager, current_user

from blueprints import General, Authentication, Tracks, MonthGoals, Charts, Users, MonthGoalsDistance, MonthGoalsCount, \
    Api, Achievements, Search, Maps, GpxTracks
from helpers import Helpers
from logic import Constants
from logic.DummyDataGenerator import DummyDataGenerator
from logic.model.Track import Track
from logic.model.User import User, Language, create_user, TrackInfoItem, TrackInfoItemType
from logic.model.db import db

LOGGER = DefaultLogger().create_logger_if_not_exists(Constants.APP_NAME)


class SportTracker(FlaskBaseApp):
    def __init__(self, appName: str, rootDir: str, logger: logging.Logger, isDebug: bool, generateDummyData: bool):
        super().__init__(appName, rootDir, logger, serveFavicon=True)

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
        app.config["SQLALCHEMY_DATABASE_URI"] = self._settings['database']['uri']

        db.init_app(app)

        with app.app_context():
            db.create_all()
            self.__create_admin_user()

            if self._generateDummyData:
                dummyDataGenerator = DummyDataGenerator()
                dummyDataGenerator.generate()

        @app.context_processor
        def inject_version_name() -> dict[str, Any]:
            return {'versionName': self._version['name']}

        def format_duration(value: int | None) -> str:
            return Helpers.format_duration(value)

        def format_pace(track: Track) -> str:
            speed = int(track.duration / (track.distance / 1000))

            minutes = speed // 60
            seconds = speed % 60
            return f'{minutes}:{str(seconds).zfill(2)}'

        @app.context_processor
        def utility_processor():
            def is_track_info_item_activated(name: str) -> bool:
                trackInfoItem = (TrackInfoItem.query
                                 .filter(TrackInfoItem.user_id == current_user.id)
                                 .filter(TrackInfoItem.type == TrackInfoItemType(name))
                                 .first())
                return trackInfoItem.is_activated

            return {'is_track_info_item_activated': is_track_info_item_activated}

        app.add_template_filter(format_duration)
        app.add_template_filter(format_pace)

        login_manager = LoginManager()
        login_manager.login_view = 'authentication.login'
        login_manager.init_app(app)

        @login_manager.user_loader
        def load_user(user_id):
            return User.query.get(int(user_id))

        app.config['LANGUAGES'] = {
            Language.ENGLISH.shortCode: Language.ENGLISH.localizedName,
            Language.GERMAN.shortCode: Language.GERMAN.localizedName
        }
        app.config['BABEL_TRANSLATION_DIRECTORIES'] = os.path.join(currentDirectory, 'localization')

        rootDirectory = os.path.dirname(currentDirectory)
        app.config['UPLOAD_FOLDER'] = os.path.join(rootDirectory, 'uploads')

        def get_locale():
            if current_user.is_authenticated:
                return current_user.language.shortCode

            return request.accept_languages.best_match(app.config['LANGUAGES'].keys())

        Babel(app, locale_selector=get_locale)

        return app

    def __create_admin_user(self):
        if User.query.filter_by(username='admin').first() is None:
            LOGGER.debug(f'Creating admin user')
            password = self.__generate_password()
            LOGGER.info(f'Created default admin user with password: "{password}".'
                        f' CAUTION: password is only shown once. Save it now!')

            create_user(username='admin', password=password, isAdmin=True, language=Language.ENGLISH)

    @staticmethod
    def __generate_password() -> str:
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for i in range(20))

    def _register_blueprints(self, app):
        app.register_blueprint(Authentication.construct_blueprint())
        app.register_blueprint(General.construct_blueprint())
        app.register_blueprint(Tracks.construct_blueprint(app.config['UPLOAD_FOLDER']))
        app.register_blueprint(MonthGoals.construct_blueprint())
        app.register_blueprint(MonthGoalsDistance.construct_blueprint())
        app.register_blueprint(MonthGoalsCount.construct_blueprint())
        app.register_blueprint(Charts.construct_blueprint())
        app.register_blueprint(Users.construct_blueprint())
        app.register_blueprint(Api.construct_blueprint(self._version))
        app.register_blueprint(Achievements.construct_blueprint())
        app.register_blueprint(Search.construct_blueprint())
        app.register_blueprint(GpxTracks.construct_blueprint(app.config['UPLOAD_FOLDER']))
        app.register_blueprint(Maps.construct_blueprint())


@click.command()
@click.option('--debug', '-d', is_flag=True, help="Enable debug mode")
@click.option('--dummy', '-dummy', is_flag=True, help="Generate dummy tracks")
def start(debug, dummy):
    server = SportTracker(Constants.APP_NAME, os.path.dirname(__file__), LOGGER, debug, dummy)
    server.start_server()


if __name__ == '__main__':
    start()
