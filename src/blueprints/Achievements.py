import logging

from flask import Blueprint, render_template
from flask_babel import gettext
from flask_login import login_required

from helpers import Helpers
from logic import Constants
from logic.AchievementCalculator import AchievementCalculator
from logic.model.Achievement import Achievement
from logic.model.Track import TrackType

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

            streak = AchievementCalculator.get_streaks_by_type(trackType)
            achievementList.append(
                Achievement(
                    icon='sports_score',
                    color=trackType.border_color,  # type: ignore[attr-defined]
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
                    color=trackType.border_color,  # type: ignore[attr-defined]
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
                    color=trackType.border_color,  # type: ignore[attr-defined]
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
                    color=trackType.border_color,  # type: ignore[attr-defined]
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
