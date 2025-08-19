import logging
import os
import secrets
import string
import tempfile
from datetime import datetime
from http import HTTPStatus
from typing import Any

import click
import flask_babel
from TheCodeLabs_BaseUtils.DefaultLogger import DefaultLogger
from TheCodeLabs_FlaskUtils import FlaskBaseApp
from alembic.runtime.migration import MigrationContext
from flask import Flask, request, abort, redirect, url_for
from flask_babel import Babel
from flask_login import LoginManager, current_user
from flask_migrate import upgrade, stamp

from sporttracker.api import Api
from sporttracker.api.Api import API_BLUEPRINT_NAME
from sporttracker.blueprints import (
    General,
    Authentication,
    Charts,
    Users,
    Achievements,
    Search,
    Maps,
    GpxTracks,
    Settings,
    AnnualAchievements,
    Notifications,
)
from sporttracker.quickFilter import QuickFilterBlueprint
from sporttracker.helpers import Helpers
from sporttracker.helpers.SettingsChecker import SettingsChecker
from sporttracker.logic import Constants
from sporttracker.logic.DummyDataGenerator import DummyDataGenerator
from sporttracker.logic.GpxService import GpxService
from sporttracker.logic.model.CustomWorkoutField import CustomWorkoutFieldType
from sporttracker.workout import WorkoutBlueprint
from sporttracker.workout.distance import DistanceWorkoutBlueprint
from sporttracker.workout.distance.DistanceWorkoutEntity import DistanceWorkout
from sporttracker.workout.fitness import FitnessWorkoutBlueprint
from sporttracker.workout.fitness.FitnessWorkoutCategory import FitnessWorkoutCategoryType
from sporttracker.workout.fitness.FitnessWorkoutType import FitnessWorkoutType
from sporttracker.logic.model.NotificationType import NotificationType
from sporttracker.longDistanceTour import LongDistanceTourBlueprint
from sporttracker.plannedTour import PlannedTourBlueprint
from sporttracker.plannedTour.TravelDirection import TravelDirection
from sporttracker.plannedTour.TravelType import TravelType
from sporttracker.logic.model.User import (
    User,
    Language,
    create_user,
    DistanceWorkoutInfoItem,
    DistanceWorkoutInfoItemType,
)
from sporttracker.workout.WorkoutType import WorkoutType
from sporttracker.logic.model.db import db, migrate
from sporttracker.workout.distance.DistanceWorkoutService import DistanceWorkoutService
from sporttracker.workout.fitness.FitnessWorkoutService import FitnessWorkoutService
from sporttracker.longDistanceTour.LongDistanceTourService import LongDistanceTourService
from sporttracker.logic.service.NotificationService import NotificationService
from sporttracker.logic.service.NtfyService import NtfyService
from sporttracker.plannedTour.PlannedTourService import PlannedTourService
from sporttracker.logic.tileHunting.MaxSquareCache import MaxSquareCache
from sporttracker.logic.tileHunting.NewVisitedTileCache import NewVisitedTileCache
from sporttracker.maintenance import MaintenanceBlueprint, MaintenanceEventInstanceBlueprint
from sporttracker.monthGoal import (
    MonthGoalBlueprint,
    MonthGoalsDistanceBlueprint,
    MonthGoalsCountBlueprint,
    MonthGoalsDurationBlueprint,
)

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

        SettingsChecker(self._settings).check()

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
        app.config['DATA_FOLDER'] = os.path.join(rootDirectory, 'data')
        app.config['TEMP_FOLDER'] = os.path.join(tempfile.gettempdir(), 'sporttracker_temp')

        app.config['NEW_VISITED_TILE_CACHE'] = NewVisitedTileCache()
        app.config['MAX_SQUARE_CACHE'] = MaxSquareCache()
        app.config['GPX_SERVICE'] = GpxService(
            app.config['DATA_FOLDER'],
            app.config['NEW_VISITED_TILE_CACHE'],
            app.config['MAX_SQUARE_CACHE'],
        )
        notificationService = NotificationService()
        app.config['NOTIFICATION_SERVICE'] = notificationService

        distanceWorkoutService = DistanceWorkoutService(
            app.config['GPX_SERVICE'], app.config['TEMP_FOLDER'], self._settings['tileHunting'], notificationService
        )
        app.config['DISTANCE_WORKOUT_SERVICE'] = distanceWorkoutService

        ntfyService = NtfyService()
        notificationService.add_listener(ntfyService)

        app.config['FITNESS_WORKOUT_SERVICE'] = FitnessWorkoutService()

        app.config['PLANNED_TOUR_SERVICE'] = PlannedTourService(
            app.config['GPX_SERVICE'],
            self._settings['gpxPreviewImages'],
            self._settings['tileHunting'],
            notificationService,
        )

        app.config['LONG_DISTANCE_TOUR_SERVICE'] = LongDistanceTourService(
            app.config['GPX_SERVICE'],
            self._settings['gpxPreviewImages'],
            app.config['PLANNED_TOUR_SERVICE'],
            notificationService,
        )

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
                'workoutTypes': [x for x in WorkoutType],
                'distanceWorkoutTypes': [x for x in WorkoutType.get_distance_workout_types()],
                'workoutTypesByName': {x.name: x for x in WorkoutType},
                'languages': [x for x in Language],
                'customWorkoutFieldTypes': [x for x in CustomWorkoutFieldType],
                'travelTypes': [x for x in TravelType],
                'travelDirections': [x for x in TravelDirection],
                'totalNumberOfNotifications': NotificationService.get_total_number_of_notifications(),
                'currentYear': datetime.now().year,
                'fitnessWorkoutTypes': [x for x in FitnessWorkoutType],
                'fitnessWorkoutCategoryTypes': [x for x in FitnessWorkoutCategoryType],
                'isDebug': self._isDebug,
                'notificationTypes': NotificationType.get_sorted(),
            }

        def format_decimal(value: int | float, decimals: int = 1) -> str:
            return Helpers.format_decimal(value, decimals)

        def format_date(value: datetime) -> str:
            return flask_babel.format_date(value, 'short')

        def format_duration(value: int | None) -> str:
            return Helpers.format_duration(value)

        def format_pace(distanceWorkout: DistanceWorkout) -> str:
            speed = int(distanceWorkout.duration / (distanceWorkout.distance / 1000))

            minutes = speed // 60
            seconds = speed % 60
            return f'{minutes}:{str(seconds).zfill(2)}'

        def check_all_items_included(allItemsList: list, listToCheck: list) -> bool:
            return all(item in listToCheck for item in allItemsList)

        @app.context_processor
        def utility_processor():
            def is_workout_info_item_activated(name: str) -> bool:
                distanceWorkoutInfoItem = (
                    DistanceWorkoutInfoItem.query.filter(DistanceWorkoutInfoItem.user_id == current_user.id)
                    .filter(DistanceWorkoutInfoItem.type == DistanceWorkoutInfoItemType(name))
                    .first()
                )
                return distanceWorkoutInfoItem.is_activated

            return {'is_workout_info_item_activated': is_workout_info_item_activated}

        app.add_template_filter(format_decimal)
        app.add_template_filter(format_date)
        app.add_template_filter(format_duration)
        app.add_template_filter(format_pace)
        app.add_template_filter(check_all_items_included)

        login_manager = LoginManager()
        login_manager.login_view = 'authentication.login'
        login_manager.refresh_view = 'authentication.logout'
        login_manager.init_app(app)

        @login_manager.user_loader
        def load_user(user_id):
            return db.session.get(User, int(user_id))

        @login_manager.unauthorized_handler
        def unauthorized():
            if request.blueprint == API_BLUEPRINT_NAME:
                if request.endpoint not in ['api.apiIndex', 'api.docs']:
                    abort(HTTPStatus.UNAUTHORIZED)

            return redirect(url_for('authentication.login', next=request.url))

        app.config['LANGUAGES'] = {
            Language.ENGLISH.shortCode: Language.ENGLISH.localized_name,
            Language.GERMAN.shortCode: Language.GERMAN.localized_name,
        }
        app.config['BABEL_TRANSLATION_DIRECTORIES'] = os.path.join(currentDirectory, 'localization')

        def get_locale():
            if current_user is None or not hasattr(current_user, 'is_authenticated'):
                return Language.ENGLISH.shortCode

            if current_user.is_authenticated:
                return current_user.language.shortCode

            return request.accept_languages.best_match(app.config['LANGUAGES'].keys())

        Babel(app, locale_selector=get_locale)

        if self._prepareDatabase:
            with app.app_context():
                self.__create_admin_user()

                if self._generateDummyData:
                    if User.query.count() > 1:
                        raise RuntimeError('Could not generate dummy data because there are already existing users!')

                    dummyDataGenerator = DummyDataGenerator(
                        app.config['GPX_SERVICE'], app.config['NOTIFICATION_SERVICE']
                    )
                    dummyDataGenerator.generate()

        return app

    def __create_admin_user(self):
        if User.query.with_entities(User.id).filter_by(username='admin').first() is None:
            LOGGER.debug('Creating admin user')
            password = self.__generate_password()
            LOGGER.info(
                f'Created default admin user with password: "{password}".'
                f' CAUTION: password is only shown once. Save it now!'
            )

            create_user(username='admin', password=password, isAdmin=True, language=Language.ENGLISH)

    @staticmethod
    def __generate_password() -> str:
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for i in range(20))

    def _register_blueprints(self, app):
        app.register_blueprint(Authentication.construct_blueprint())
        app.register_blueprint(General.construct_blueprint())
        app.register_blueprint(WorkoutBlueprint.construct_blueprint())
        app.register_blueprint(
            DistanceWorkoutBlueprint.construct_blueprint(
                app.config['GPX_SERVICE'],
                app.config['TEMP_FOLDER'],
                app.config['DISTANCE_WORKOUT_SERVICE'],
            )
        )
        app.register_blueprint(FitnessWorkoutBlueprint.construct_blueprint(app.config['FITNESS_WORKOUT_SERVICE']))
        app.register_blueprint(MonthGoalBlueprint.construct_blueprint())
        app.register_blueprint(MonthGoalsDistanceBlueprint.construct_blueprint())
        app.register_blueprint(MonthGoalsCountBlueprint.construct_blueprint())
        app.register_blueprint(MonthGoalsDurationBlueprint.construct_blueprint())
        app.register_blueprint(
            Charts.construct_blueprint(
                app.config['NEW_VISITED_TILE_CACHE'],
                app.config['MAX_SQUARE_CACHE'],
                app.config['DISTANCE_WORKOUT_SERVICE'],
            )
        )
        app.register_blueprint(Users.construct_blueprint())
        app.register_blueprint(Settings.construct_blueprint())
        app.register_blueprint(
            Api.construct_blueprint(
                app.config['GPX_SERVICE'],
                self._settings['tileHunting'],
                app.config['DISTANCE_WORKOUT_SERVICE'],
                app.config['FITNESS_WORKOUT_SERVICE'],
            )
        )
        app.register_blueprint(Achievements.construct_blueprint())
        app.register_blueprint(Search.construct_blueprint())
        app.register_blueprint(
            GpxTracks.construct_blueprint(
                app.config['GPX_SERVICE'], app.config['DISTANCE_WORKOUT_SERVICE'], self._settings['gpxPreviewImages']
            )
        )
        app.register_blueprint(
            Maps.construct_blueprint(
                self._settings['tileHunting'],
                app.config['NEW_VISITED_TILE_CACHE'],
                app.config['MAX_SQUARE_CACHE'],
                app.config['DISTANCE_WORKOUT_SERVICE'],
                self._settings['gpxPreviewImages'],
                app.config['PLANNED_TOUR_SERVICE'],
            )
        )
        app.register_blueprint(QuickFilterBlueprint.construct_blueprint())
        app.register_blueprint(MaintenanceBlueprint.construct_blueprint())
        app.register_blueprint(MaintenanceEventInstanceBlueprint.construct_blueprint())
        app.register_blueprint(
            PlannedTourBlueprint.construct_blueprint(
                app.config['GPX_SERVICE'], self._settings['gpxPreviewImages'], app.config['PLANNED_TOUR_SERVICE']
            )
        )
        app.register_blueprint(
            LongDistanceTourBlueprint.construct_blueprint(
                self._settings['gpxPreviewImages'], app.config['LONG_DISTANCE_TOUR_SERVICE']
            )
        )
        app.register_blueprint(AnnualAchievements.construct_blueprint())
        app.register_blueprint(Notifications.construct_blueprint(app.config['NOTIFICATION_SERVICE']))

    def __prepare_database(self, app):
        with app.app_context():
            db.create_all()


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
    server = SportTracker(Constants.APP_NAME, os.path.dirname(__file__), LOGGER, False, False, False)
    return server.init_app()


@click.command()
@click.option('--debug', '-d', is_flag=True, help='Enable debug mode')
@click.option('--dummy', '-dummy', is_flag=True, help='Generate dummy workouts')
def start(debug, dummy):
    sportTracker = SportTracker(Constants.APP_NAME, os.path.dirname(__file__), LOGGER, debug, dummy, True)
    sportTracker.start_server()


if __name__ == '__main__':
    start()
