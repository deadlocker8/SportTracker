import logging
from datetime import datetime
from statistics import mean

from flask import Blueprint, render_template, redirect, url_for
from flask_babel import gettext
from flask_login import login_required, current_user

from sporttracker.helpers import Helpers
from sporttracker.logic import Constants
from sporttracker.logic.AchievementCalculator import AchievementCalculator
from sporttracker.logic.model.Achievement import (
    AnnualAchievement,
    AnnualAchievementDifferenceType,
    AllYearData,
)
from sporttracker.logic.model.Track import get_available_years
from sporttracker.logic.model.TrackType import TrackType

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
            selectedYear=year,
            availableYears=get_available_years(current_user.id),
        )

    def __get_annual_achievements(year: int) -> dict[TrackType, list[AnnualAchievement]]:
        result = {}

        availableYears = get_available_years(current_user.id)
        yearNames = [str(year) for year in availableYears]

        for trackType in TrackType:
            achievementList = []

            if trackType.supports_distance:
                achievementList.append(
                    __create_achievement_total_distance(availableYears, trackType, year, yearNames)
                )

                achievementList.append(
                    __create_achievement_total_duration(availableYears, trackType, year, yearNames)
                )

                achievementList.append(
                    __create_achievement_track_count(
                        availableYears,
                        trackType,
                        year,
                        yearNames,
                        gettext('Number Of Tracks'),
                        'fa-route',
                        True,
                    )
                )

                achievementList.append(
                    __create_achievement_longest_track(availableYears, trackType, year, yearNames)
                )

                achievementList.append(
                    __create_achievement_average_speed(availableYears, trackType, year, yearNames)
                )
            else:
                achievementList.append(
                    __create_achievement_total_duration(availableYears, trackType, year, yearNames)
                )

                achievementList.append(
                    __create_achievement_track_count(
                        availableYears,
                        trackType,
                        year,
                        yearNames,
                        gettext('Number Of Workouts'),
                        'fitness_center',
                        False,
                    )
                )

                achievementList.append(
                    __create_achievement_longest_duration(
                        availableYears, trackType, year, yearNames
                    )
                )

            result[trackType] = achievementList

        return result

    def __create_achievement_total_distance(
        availableYears: list[int], trackType: TrackType, year: int, yearNames: list[str]
    ) -> AnnualAchievement:
        values = []
        totalDistance = 0.0
        totalDistancePreviousYear = 0.0

        for currentYear in availableYears:
            value = AchievementCalculator.get_total_distance_by_type_and_year(
                trackType, currentYear
            )
            values.append(value)

            if currentYear == year:
                totalDistance = value
            elif currentYear == year - 1:
                totalDistancePreviousYear = value

        totalDistanceDifference = totalDistance - totalDistancePreviousYear
        totalDistanceAllYearData = AllYearData(
            year_names=yearNames,
            values=values,
            labels=[__format_distance(x) for x in values],
            min=__format_distance(min(values)) if values else '-',
            max=__format_distance(max(values)) if values else '-',
            sum=__format_distance(sum(values)) if values else '-',
            average=__format_distance(mean(values)) if values else '-',
        )

        return AnnualAchievement(
            icon='map',
            is_font_awesome_icon=False,
            is_outlined_icon=False,
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

    def __create_achievement_total_duration(
        availableYears: list[int], trackType: TrackType, year: int, yearNames: list[str]
    ) -> AnnualAchievement:
        values = []
        totalDuration = 0
        totalDurationPreviousYear = 0

        for currentYear in availableYears:
            value = AchievementCalculator.get_total_duration_by_type_and_year(
                trackType, currentYear
            )
            values.append(value)
            if currentYear == year:
                totalDuration = value
            elif currentYear == year - 1:
                totalDurationPreviousYear = value

        totalDurationDifference = totalDuration - totalDurationPreviousYear
        totalDurationAllYearData = AllYearData(
            year_names=yearNames,
            values=[x / 3600 for x in values],
            labels=[__format_duration(x) for x in values],
            min=__format_duration(min(values)) if values else '-',
            max=__format_duration(max(values)) if values else '-',
            sum=__format_duration(sum(values)) if values else '-',
            average=__format_duration(mean(values)) if values else '-',
        )
        return AnnualAchievement(
            icon='timer',
            is_font_awesome_icon=False,
            is_outlined_icon=True,
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

    def __create_achievement_track_count(
        availableYears: list[int],
        trackType: TrackType,
        year: int,
        yearNames: list[str],
        title: str,
        icon: str,
        is_font_awesome_icon: bool,
    ) -> AnnualAchievement:
        values = []
        totalTrackCount = 0
        totalTrackCountPreviousYear = 0

        for currentYear in availableYears:
            value = AchievementCalculator.get_total_number_of_tracks_by_type_and_year(
                trackType, currentYear
            )
            values.append(value)
            if currentYear == year:
                totalTrackCount = value
            elif currentYear == year - 1:
                totalTrackCountPreviousYear = value

        totalTrackCountDifference = totalTrackCount - totalTrackCountPreviousYear
        totalTrackCountAllYearData = AllYearData(
            year_names=yearNames,
            values=values,
            labels=[__format_count(x) for x in values],
            min=__format_count(min(values)) if values else '-',
            max=__format_count(max(values)) if values else '-',
            sum=__format_count(sum(values)) if values else '-',
            average=__format_count(mean(values)) if values else '-',
        )
        return AnnualAchievement(
            icon=icon,
            is_font_awesome_icon=is_font_awesome_icon,
            is_outlined_icon=False,
            color=trackType.border_color,
            title=title,
            description=str(totalTrackCount),
            difference_to_previous_year=str(abs(totalTrackCountDifference)),
            difference_type=AnnualAchievementDifferenceType.get_by_difference(
                totalTrackCountDifference
            ),
            all_year_data=totalTrackCountAllYearData,
            unit='',
        )

    def __create_achievement_longest_track(
        availableYears: list[int], trackType: TrackType, year: int, yearNames: list[str]
    ) -> AnnualAchievement:
        values = []
        longestTrack = 0.0
        longestTrackPreviousYear = 0.0

        for currentYear in availableYears:
            value = AchievementCalculator.get_longest_distance_by_type_and_year(
                trackType, currentYear
            )
            values.append(value)
            if currentYear == year:
                longestTrack = value
            elif currentYear == year - 1:
                longestTrackPreviousYear = value

        longestTrackDifference = longestTrack - longestTrackPreviousYear
        longestTrackAllYearData = AllYearData(
            year_names=yearNames,
            values=values,
            labels=[__format_distance(x) for x in values],
            min=__format_distance(min(values)) if values else '-',
            max=__format_distance(max(values)) if values else '-',
            sum=__format_distance(sum(values)) if values else '-',
            average=__format_distance(mean(values)) if values else '-',
        )

        return AnnualAchievement(
            icon='route',
            is_font_awesome_icon=False,
            is_outlined_icon=False,
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

    def __create_achievement_average_speed(
        availableYears: list[int], trackType: TrackType, year: int, yearNames: list[str]
    ) -> AnnualAchievement:
        values = []
        averageSpeed = 0.0
        averageSpeedPreviousYear = 0.0

        for currentYear in availableYears:
            value = AchievementCalculator.get_average_speed_by_type_and_year(trackType, currentYear)
            values.append(value)
            if currentYear == year:
                averageSpeed = value
            elif currentYear == year - 1:
                averageSpeedPreviousYear = value

        averageSpeedDifference = averageSpeed - averageSpeedPreviousYear
        averageSpeedAllYearData = AllYearData(
            year_names=yearNames,
            values=values,
            labels=[__format_speed(x) for x in values],
            min=__format_speed(min(values)) if values else '-',
            max=__format_speed(max(values)) if values else '-',
            sum=__format_speed(sum(values)) if values else '-',
            average=__format_speed(mean(values)) if values else '-',
        )

        return AnnualAchievement(
            icon='speed',
            is_font_awesome_icon=False,
            is_outlined_icon=False,
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

    def __create_achievement_longest_duration(
        availableYears: list[int], trackType: TrackType, year: int, yearNames: list[str]
    ) -> AnnualAchievement:
        values = []
        longestDuration = 0
        longestDurationPreviousYear = 0

        for currentYear in availableYears:
            value = AchievementCalculator.get_longest_duration_by_type_and_year(
                trackType, currentYear
            )
            values.append(value)
            if currentYear == year:
                longestDuration = value
            elif currentYear == year - 1:
                longestDurationPreviousYear = value

        longestDurationDifference = longestDuration - longestDurationPreviousYear
        longestDurationAllYearData = AllYearData(
            year_names=yearNames,
            values=values,
            labels=[__format_duration(x) for x in values],
            min=__format_duration(min(values)) if values else '-',
            max=__format_duration(max(values)) if values else '-',
            sum=__format_duration(sum(values)) if values else '-',
            average=__format_duration(mean(values)) if values else '-',
        )

        return AnnualAchievement(
            icon='schedule',
            is_font_awesome_icon=False,
            is_outlined_icon=False,
            color=trackType.border_color,
            title=gettext('Longest Duration'),
            description=__format_duration(longestDuration),
            difference_to_previous_year=__format_duration(abs(longestDurationDifference)),
            difference_type=AnnualAchievementDifferenceType.get_by_difference(
                longestDurationDifference
            ),
            all_year_data=longestDurationAllYearData,
            unit='km',
        )

    return annualAchievements


def __format_distance(distance: float) -> str:
    return '{distance} km'.format(distance=Helpers.format_decimal(distance, decimals=2))


def __format_duration(duration: int | float) -> str:
    return '{duration} h'.format(duration=Helpers.format_duration(int(duration)))


def __format_speed(speed: float) -> str:
    return '{speed} km/h'.format(speed=Helpers.format_decimal(speed, decimals=2))


def __format_count(count: float) -> str:
    return f'{int(count)}'
