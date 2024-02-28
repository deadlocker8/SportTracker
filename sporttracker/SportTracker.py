import logging
import os
import secrets
import string
from datetime import datetime
from typing import Any

import click
import flask_babel
from TheCodeLabs_BaseUtils.DefaultLogger import DefaultLogger
from TheCodeLabs_FlaskUtils import FlaskBaseApp
from alembic.runtime.migration import MigrationContext
from flask import Flask, request
from flask_babel import Babel
from flask_login import LoginManager, current_user
from flask_migrate import upgrade, stamp

from sporttracker.blueprints import (
    General,
    Authentication,
    Tracks,
    MonthGoals,
    Charts,
    Users,
    MonthGoalsDistance,
    MonthGoalsCount,
    Api,
    Achievements,
    Search,
    Maps,
    GpxTracks,
    Settings,
)
from sporttracker.helpers import Helpers
from sporttracker.logic import Constants
from sporttracker.logic.DummyDataGenerator import DummyDataGenerator
from sporttracker.logic.model.CustomTrackField import CustomTrackFieldType
from sporttracker.logic.model.Track import Track, TrackType
from sporttracker.logic.model.User import (
    User,
    Language,
    create_user,
    TrackInfoItem,
    TrackInfoItemType,
)
from sporttracker.logic.model.db import db, migrate

LOGGER = DefaultLogger().create_logger_if_not_exists(Constants.APP_NAME)
LOGGER.propagate = False
DefaultLogger.configure_logger(logging.getLogger('root'))


class SportTracker(FlaskBaseApp):
    def __init__(
        self,
        appName: str,
        rootDir: str,
        logger: logging.Logger,
        isDebug: bool,
        generateDummyData: bool,
        prepareDatabase: bool,
        settingsPath: str = '../settings.json',
    ):
        os.chdir(rootDir)
        super().__init__(appName, rootDir, logger, settingsPath=settingsPath, serveFavicon=True)

        self._isDebug = isDebug
        self._generateDummyData = generateDummyData
        self._prepareDatabase = prepareDatabase

        loggingSettings = self._settings['logging']
        if loggingSettings['enableRotatingLogFile']:
            DefaultLogger.add_rotating_file_handler(
                LOGGER,
                fileName=loggingSettings['fileName'],
                maxBytes=loggingSettings['maxBytes'],
                backupCount=loggingSettings['numberOfBackups'],
            )

    def _create_flask_app(self):
        app = Flask(self._rootDir)
        app.debug = self._isDebug

        currentDirectory = os.path.abspath(os.path.dirname(__file__))
        app.config['SQLALCHEMY_DATABASE_URI'] = self._settings['database']['uri']

        db.init_app(app)
        migrate.init_app(app, db)

        rootDirectory = os.path.dirname(currentDirectory)
        app.config['UPLOAD_FOLDER'] = os.path.join(rootDirectory, 'uploads')

        if self._prepareDatabase:
            self.__prepare_database(app)

        with app.app_context():
            context = MigrationContext.configure(db.engine.connect())
            currentDatabaseRevision = context.get_current_revision()
            if currentDatabaseRevision is None:
                stamp(revision=Constants.LATEST_DATABASE_REVISION)
            elif currentDatabaseRevision == Constants.LATEST_DATABASE_REVISION:
                LOGGER.info('No database upgrade needed')
            else:
                LOGGER.info('Upgrading database...')
                upgrade()
                LOGGER.info('Upgrading database DONE')

        @app.context_processor
        def inject_static_access() -> dict[str, Any]:
            return {
                'versionName': self._version['name'],
                'trackTypes': [x for x in TrackType],
                'languages': [x for x in Language],
                'customTrackFieldTypes': [x for x in CustomTrackFieldType],
            }

        def format_decimal(value: int | float, decimals: int = 1) -> str:
            return Helpers.format_decimal(value, decimals)

        def format_date(value: datetime) -> str:
            return flask_babel.format_date(value, 'short')

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
                trackInfoItem = (
                    TrackInfoItem.query.filter(TrackInfoItem.user_id == current_user.id)
                    .filter(TrackInfoItem.type == TrackInfoItemType(name))
                    .first()
                )
                return trackInfoItem.is_activated

            return {'is_track_info_item_activated': is_track_info_item_activated}

        app.add_template_filter(format_decimal)
        app.add_template_filter(format_date)
        app.add_template_filter(format_duration)
        app.add_template_filter(format_pace)

        login_manager = LoginManager()
        login_manager.login_view = 'authentication.login'
        login_manager.init_app(app)

        @login_manager.user_loader
        def load_user(user_id):
            return db.session.get(User, int(user_id))

        app.config['LANGUAGES'] = {
            Language.ENGLISH.shortCode: Language.ENGLISH.localized_name,
            Language.GERMAN.shortCode: Language.GERMAN.localized_name,
        }
        app.config['BABEL_TRANSLATION_DIRECTORIES'] = os.path.join(currentDirectory, 'localization')

        def get_locale():
            if current_user.is_authenticated:
                return current_user.language.shortCode

            return request.accept_languages.best_match(app.config['LANGUAGES'].keys())

        Babel(app, locale_selector=get_locale)

        return app

    def __create_admin_user(self):
        if User.query.filter_by(username='admin').first() is None:
            LOGGER.debug('Creating admin user')
            password = self.__generate_password()
            LOGGER.info(
                f'Created default admin user with password: "{password}".'
                f' CAUTION: password is only shown once. Save it now!'
            )

            create_user(
                username='admin', password=password, isAdmin=True, language=Language.ENGLISH
            )

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
        app.register_blueprint(Settings.construct_blueprint())
        app.register_blueprint(Api.construct_blueprint(self._version, app.config['UPLOAD_FOLDER']))
        app.register_blueprint(Achievements.construct_blueprint())
        app.register_blueprint(Search.construct_blueprint())
        app.register_blueprint(GpxTracks.construct_blueprint(app.config['UPLOAD_FOLDER']))
        app.register_blueprint(Maps.construct_blueprint())

    def __prepare_database(self, app):
        with app.app_context():
            db.create_all()
            self.__create_admin_user()

            if self._generateDummyData:
                dummyDataGenerator = DummyDataGenerator(app.config['UPLOAD_FOLDER'])
                dummyDataGenerator.generate()


def create_test_app():
    server = SportTracker(
        Constants.APP_NAME,
        os.path.dirname(__file__),
        LOGGER,
        False,
        False,
        True,
        settingsPath='../settings-test.json',
    )
    return server.init_app()


# needed for creation of database revisions
def create_app():
    server = SportTracker(
        Constants.APP_NAME, os.path.dirname(__file__), LOGGER, False, False, False
    )
    return server.init_app()


@click.command()
@click.option('--debug', '-d', is_flag=True, help='Enable debug mode')
@click.option('--dummy', '-dummy', is_flag=True, help='Generate dummy tracks')
def start(debug, dummy):
    sportTracker = SportTracker(
        Constants.APP_NAME, os.path.dirname(__file__), LOGGER, debug, dummy, True
    )
    sportTracker.start_server()


if __name__ == '__main__':
    start()
