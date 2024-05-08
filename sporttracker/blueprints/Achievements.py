import logging
from datetime import datetime

from flask import Blueprint, render_template
from flask_babel import gettext
from flask_login import login_required

from sporttracker.helpers import Helpers
from sporttracker.logic import Constants
from sporttracker.logic.AchievementCalculator import AchievementCalculator
from sporttracker.logic.model.Achievement import Achievement
from sporttracker.logic.model.Track import TrackType

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint():
    achievements = Blueprint(
        'achievements', __name__, static_folder='static', url_prefix='/achievements'
    )

    @achievements.route('/')
    @login_required
    def showAchievements():
        return render_template('achievements.jinja2', achievements=__get_achievements())

    def __get_achievements() -> dict[TrackType, list[Achievement]]:
        result = {}

        for trackType in TrackType:
            achievementList = []

            streak = AchievementCalculator.get_streaks_by_type(trackType, datetime.now().date())
            achievementList.append(
                Achievement(
                    icon='sports_score',
                    is_font_awesome_icon=False,
                    color=trackType.border_color,
                    title=gettext('Month Goal Streak'),
                    description=gettext(
                        'You have achieved all your monthly goals for <span class="fw-bold">{currentStreak}</span> '
                        'months in a row!<br>(Best: <span class="fw-bold">{maxStreak}</span>)'
                    ).format(currentStreak=streak[1], maxStreak=streak[0]),
                )
            )
            achievementList.append(
                Achievement(
                    icon='route',
                    is_font_awesome_icon=False,
                    color=trackType.border_color,
                    title=gettext('Longest Track'),
                    description=gettext(
                        'You completed <span class="fw-bold">{longestTrack} km</span> in one trip!'
                    ).format(
                        longestTrack=Helpers.format_decimal(
                            AchievementCalculator.get_longest_distance_by_type(trackType),
                            decimals=2,
                        )
                    ),
                )
            )
            achievementList.append(
                Achievement(
                    icon='map',
                    is_font_awesome_icon=False,
                    color=trackType.border_color,
                    title=gettext('Total Distance'),
                    description=gettext(
                        'You completed a total of <span class="fw-bold">{totalDistance} km</span>!'
                    ).format(
                        totalDistance=Helpers.format_decimal(
                            AchievementCalculator.get_total_distance_by_type(trackType), decimals=2
                        )
                    ),
                )
            )
            bestMonth = AchievementCalculator.get_best_month_by_type(trackType)
            achievementList.append(
                Achievement(
                    icon='calendar_month',
                    is_font_awesome_icon=False,
                    color=trackType.border_color,
                    title=gettext('Best Month'),
                    description=gettext(
                        '<span class="fw-bold">{bestMonthName}</span> was your best month with <span class="fw-bold">'
                        '{bestMonthDistance} km</span>!'
                    ).format(
                        bestMonthName=bestMonth[0],
                        bestMonthDistance=Helpers.format_decimal(bestMonth[1], decimals=2),
                    ),
                )
            )
            result[trackType] = achievementList
        return result

    return achievements
