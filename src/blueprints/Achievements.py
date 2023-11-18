import logging

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy import func

from logic import Constants
from logic.model.Models import BikingTrack, db, RunningTrack

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint():
    achievements = Blueprint('achievements', __name__, static_folder='static', url_prefix='/achievements')

    @achievements.route('/')
    @login_required
    def showAchievements():
        return render_template('achievements.jinja2',
                               bikingLongestTrack=__get_longest_distance_by_type(BikingTrack) / 1000,
                               bikingTotalDistance=__get_total_distance_by_type(BikingTrack) / 1000,
                               runningLongestTrack=__get_longest_distance_by_type(RunningTrack) / 1000,
                               runningTotalDistance=__get_total_distance_by_type(RunningTrack) / 1000
                               )

    def __get_longest_distance_by_type(trackClass) -> int:
        return db.session.query(func.max(trackClass.distance)).filter(
            trackClass.user_id == current_user.id).scalar() or 0

    def __get_total_distance_by_type(trackClass) -> int:
        return db.session.query(func.sum(trackClass.distance)).filter(
            trackClass.user_id == current_user.id).scalar() or 0

    return achievements
