import logging
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for
from flask_babel import gettext
from flask_login import login_required

from sporttracker.helpers import Helpers
from sporttracker.logic import Constants
from sporttracker.logic.AchievementCalculator import AchievementCalculator
from sporttracker.logic.model.Achievement import Achievement
from sporttracker.logic.model.Track import TrackType, get_available_years

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint():
    annualAchievements = Blueprint(
        'annualAchievements', __name__, static_folder='static', url_prefix='/annualAchievements'
    )

    @annualAchievements.route('/')
    @login_required
    def showAnnualAchievements():
        return redirect(
            url_for('annualAchievements.showAnnualAchievementsByYear', year=datetime.now().year)
        )

    @annualAchievements.route('/<int:year>')
    @login_required
    def showAnnualAchievementsByYear(year: int):
        return render_template(
            'annualAchievements.jinja2',
            achievements=__get_annual_achievements(year),
            currentYear=year,
            availableYears=get_available_years(),
        )

    def __get_annual_achievements(year: int) -> dict[TrackType, list[Achievement]]:
        result = {}

        for trackType in TrackType:
            achievementList = []
            achievementList.append(
                Achievement(
                    icon='map',
                    is_font_awesome_icon=False,
                    color=trackType.border_color,
                    title=gettext('Total Distance'),
                    description='{totalDistance} km'.format(
                        totalDistance=Helpers.format_decimal(
                            AchievementCalculator.get_total_distance_by_type_and_year(
                                trackType, year
                            ),
                            decimals=2,
                        )
                    ),
                )
            )
            achievementList.append(
                Achievement(
                    icon='timer',
                    is_font_awesome_icon=False,
                    color=trackType.border_color,
                    title=gettext('Total Duration'),
                    description='{totalDuration} h'.format(
                        totalDuration=Helpers.format_duration(
                            AchievementCalculator.get_total_duration_by_type_and_year(
                                trackType, year
                            )
                        )
                    ),
                )
            )
            achievementList.append(
                Achievement(
                    icon='fa-route',
                    is_font_awesome_icon=True,
                    color=trackType.border_color,
                    title=gettext('Number Of Tracks'),
                    description=str(
                        AchievementCalculator.get_total_number_of_tracks_by_type_and_year(
                            trackType, year
                        )
                    ),
                )
            )
            achievementList.append(
                Achievement(
                    icon='route',
                    is_font_awesome_icon=False,
                    color=trackType.border_color,
                    title=gettext('Longest Track'),
                    description='{longestDistance} km'.format(
                        longestDistance=Helpers.format_decimal(
                            AchievementCalculator.get_longest_distance_by_type_and_year(
                                trackType, year
                            ),
                            decimals=2,
                        )
                    ),
                )
            )
            achievementList.append(
                Achievement(
                    icon='speed',
                    is_font_awesome_icon=False,
                    color=trackType.border_color,
                    title=gettext('Average Speed'),
                    description='{averageSpeed} km/h'.format(
                        averageSpeed=Helpers.format_decimal(
                            AchievementCalculator.get_longest_distance_by_type_and_year(
                                trackType, year
                            ),
                            decimals=2,
                        )
                    ),
                )
            )
            result[trackType] = achievementList

        return result

    return annualAchievements
