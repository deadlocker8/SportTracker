import logging
from datetime import datetime
from statistics import mean

from flask import Blueprint, render_template, redirect, url_for
from flask_babel import gettext
from flask_login import login_required

from sporttracker.helpers import Helpers
from sporttracker.logic import Constants
from sporttracker.logic.AchievementCalculator import AchievementCalculator
from sporttracker.logic.model.Achievement import (
    AnnualAchievement,
    AnnualAchievementDifferenceType,
    AllYearData,
)
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

    def __get_annual_achievements(year: int) -> dict[TrackType, list[AnnualAchievement]]:
        result = {}

        availableYears = get_available_years()
        yearNames = [str(year) for year in availableYears]

        for trackType in TrackType:
            achievementList = []

            totalDistance = AchievementCalculator.get_total_distance_by_type_and_year(
                trackType, year
            )
            totalDistancePreviousYear = AchievementCalculator.get_total_distance_by_type_and_year(
                trackType, year - 1
            )
            totalDistanceDifference = totalDistance - totalDistancePreviousYear

            values = []
            for year in availableYears:
                values.append(
                    AchievementCalculator.get_total_distance_by_type_and_year(trackType, year)
                )
            totalDistanceAllYearData = AllYearData(
                year_names=yearNames,
                values=values,
                labels=[__format_distance(x) for x in values],
                min=__format_distance(min(values)) if values else '-',
                max=__format_distance(max(values)) if values else '-',
                sum=__format_distance(sum(values)) if values else '-',
                average=__format_distance(mean(values)) if values else '-',
            )

            achievementList.append(
                AnnualAchievement(
                    icon='map',
                    is_font_awesome_icon=False,
                    color=trackType.border_color,
                    title=gettext('Total Distance'),
                    description=__format_distance(totalDistance),
                    difference_to_previous_year=__format_distance(abs(totalDistanceDifference)),
                    difference_type=AnnualAchievementDifferenceType.get_by_difference(
                        totalDistanceDifference
                    ),
                    all_year_data=totalDistanceAllYearData,
                    unit='km',
                )
            )

            totalDuration = AchievementCalculator.get_total_duration_by_type_and_year(
                trackType, year
            )
            totalDurationPreviousYear = AchievementCalculator.get_total_duration_by_type_and_year(
                trackType, year - 1
            )
            totalDurationDifference = totalDuration - totalDurationPreviousYear

            values = []
            for year in availableYears:
                values.append(
                    AchievementCalculator.get_total_duration_by_type_and_year(trackType, year)
                )
            totalDurationAllYearData = AllYearData(
                year_names=yearNames,
                values=values,
                labels=[__format_duration(x) for x in values],
                min=__format_duration(min(values)) if values else '-',
                max=__format_duration(max(values)) if values else '-',
                sum=__format_duration(sum(values)) if values else '-',
                average=__format_duration(mean(values)) if values else '-',
            )

            achievementList.append(
                AnnualAchievement(
                    icon='timer',
                    is_font_awesome_icon=False,
                    color=trackType.border_color,
                    title=gettext('Total Duration'),
                    description=__format_duration(totalDuration),
                    difference_to_previous_year=__format_duration(abs(totalDurationDifference)),
                    difference_type=AnnualAchievementDifferenceType.get_by_difference(
                        totalDurationDifference
                    ),
                    all_year_data=totalDurationAllYearData,
                    unit=gettext('Hours'),
                )
            )

            totalTrackCount = AchievementCalculator.get_total_number_of_tracks_by_type_and_year(
                trackType, year
            )
            totalTrackCountPreviousYear = (
                AchievementCalculator.get_total_number_of_tracks_by_type_and_year(
                    trackType, year - 1
                )
            )
            totalTrackCountDifference = totalTrackCount - totalTrackCountPreviousYear

            values = []
            for year in availableYears:
                values.append(
                    AchievementCalculator.get_total_number_of_tracks_by_type_and_year(
                        trackType, year
                    )
                )
            totalTrackCountAllYearData = AllYearData(
                year_names=yearNames,
                values=values,
                labels=[str(x) for x in values],
                min=str(min(values)) if values else '-',
                max=str(max(values)) if values else '-',
                sum=str(sum(values)) if values else '-',
                average=str(mean(values)) if values else '-',
            )

            achievementList.append(
                AnnualAchievement(
                    icon='fa-route',
                    is_font_awesome_icon=True,
                    color=trackType.border_color,
                    title=gettext('Number Of Tracks'),
                    description=str(totalTrackCount),
                    difference_to_previous_year=str(abs(totalTrackCountDifference)),
                    difference_type=AnnualAchievementDifferenceType.get_by_difference(
                        totalTrackCountDifference
                    ),
                    all_year_data=totalTrackCountAllYearData,
                    unit='',
                )
            )

            longestTrack = AchievementCalculator.get_longest_distance_by_type_and_year(
                trackType, year
            )
            longestTrackPreviousYear = AchievementCalculator.get_longest_distance_by_type_and_year(
                trackType, year - 1
            )
            longestTrackDifference = longestTrack - longestTrackPreviousYear

            values = []
            for year in availableYears:
                values.append(
                    AchievementCalculator.get_longest_distance_by_type_and_year(trackType, year)
                )
            longestTrackAllYearData = AllYearData(
                year_names=yearNames,
                values=values,
                labels=[__format_distance(x) for x in values],
                min=__format_distance(min(values)) if values else '-',
                max=__format_distance(max(values)) if values else '-',
                sum=__format_distance(sum(values)) if values else '-',
                average=__format_distance(mean(values)) if values else '-',
            )

            achievementList.append(
                AnnualAchievement(
                    icon='route',
                    is_font_awesome_icon=False,
                    color=trackType.border_color,
                    title=gettext('Longest Track'),
                    description=__format_distance(longestTrack),
                    difference_to_previous_year=__format_distance(abs(longestTrackDifference)),
                    difference_type=AnnualAchievementDifferenceType.get_by_difference(
                        longestTrackDifference
                    ),
                    all_year_data=longestTrackAllYearData,
                    unit='km',
                )
            )

            averageSpeed = AchievementCalculator.get_average_speed_by_type_and_year(trackType, year)
            averageSpeedPreviousYear = AchievementCalculator.get_average_speed_by_type_and_year(
                trackType, year - 1
            )
            averageSpeedDifference = averageSpeed - averageSpeedPreviousYear

            values = []
            for year in availableYears:
                values.append(
                    AchievementCalculator.get_average_speed_by_type_and_year(trackType, year)
                )
            averageSpeedAllYearData = AllYearData(
                year_names=yearNames,
                values=values,
                labels=[__format_speed(x) for x in values],
                min=__format_speed(min(values)) if values else '-',
                max=__format_speed(max(values)) if values else '-',
                sum=__format_speed(sum(values)) if values else '-',
                average=__format_speed(mean(values)) if values else '-',
            )

            achievementList.append(
                AnnualAchievement(
                    icon='speed',
                    is_font_awesome_icon=False,
                    color=trackType.border_color,
                    title=gettext('Average Speed'),
                    description=__format_speed(averageSpeed),
                    difference_to_previous_year=__format_speed(abs(averageSpeedDifference)),
                    difference_type=AnnualAchievementDifferenceType.get_by_difference(
                        averageSpeedDifference
                    ),
                    all_year_data=averageSpeedAllYearData,
                    unit='km/h',
                )
            )
            result[trackType] = achievementList

        return result

    return annualAchievements


def __format_distance(distance: float) -> str:
    return '{distance} km'.format(distance=Helpers.format_decimal(distance, decimals=2))


def __format_duration(duration: int | float) -> str:
    return '{duration} h'.format(duration=Helpers.format_duration(int(duration)))


def __format_speed(speed: float) -> str:
    return '{speed} km/h'.format(speed=Helpers.format_decimal(speed, decimals=2))
