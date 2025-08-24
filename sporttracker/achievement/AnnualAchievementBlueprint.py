import logging
from datetime import datetime
from statistics import mean

from flask import Blueprint, render_template, redirect, url_for
from flask_babel import gettext
from flask_login import login_required, current_user

from sporttracker.helpers import Helpers
from sporttracker import Constants
from sporttracker.achievement.AchievementCalculator import AchievementCalculator
from sporttracker.achievement.AchievementEntity import (
    AnnualAchievement,
    AnnualAchievementDifferenceType,
    AllYearData,
)
from sporttracker.workout.WorkoutEntity import get_available_years
from sporttracker.workout.WorkoutType import WorkoutType

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint():
    annualAchievements = Blueprint(
        'annualAchievements', __name__, static_folder='static', url_prefix='/annualAchievements'
    )

    @annualAchievements.route('/')
    @login_required
    def showAnnualAchievements():
        return redirect(url_for('annualAchievements.showAnnualAchievementsByYear', year=datetime.now().year))

    @annualAchievements.route('/<int:year>')
    @login_required
    def showAnnualAchievementsByYear(year: int):
        return render_template(
            'achievement/annualAchievements.jinja2',
            achievements=__get_annual_achievements(year),
            selectedYear=year,
            availableYears=get_available_years(current_user.id),
        )

    def __get_annual_achievements(year: int) -> dict[WorkoutType, list[AnnualAchievement]]:
        result = {}

        availableYears = get_available_years(current_user.id)
        yearNames = [str(year) for year in availableYears]

        for workoutType in WorkoutType.get_distance_workout_types():
            achievementList = []

            achievementList.append(__create_achievement_total_distance(availableYears, workoutType, year, yearNames))

            achievementList.append(__create_achievement_total_duration(availableYears, workoutType, year, yearNames))

            achievementList.append(
                __create_achievement_workout_count(
                    availableYears,
                    workoutType,
                    year,
                    yearNames,
                    gettext('Number Of Workouts'),
                    'fa-route',
                    True,
                )
            )

            achievementList.append(__create_achievement_longest_workout(availableYears, workoutType, year, yearNames))

            achievementList.append(__create_achievement_average_speed(availableYears, workoutType, year, yearNames))

            result[workoutType] = achievementList

        for workoutType in WorkoutType.get_fitness_workout_types():
            achievementList = []

            achievementList.append(__create_achievement_total_duration(availableYears, workoutType, year, yearNames))

            achievementList.append(
                __create_achievement_workout_count(
                    availableYears,
                    workoutType,
                    year,
                    yearNames,
                    gettext('Number Of Workouts'),
                    'fitness_center',
                    False,
                )
            )

            achievementList.append(__create_achievement_longest_duration(availableYears, workoutType, year, yearNames))

            result[workoutType] = achievementList

        return result

    def __create_achievement_total_distance(
        availableYears: list[int], workoutType: WorkoutType, year: int, yearNames: list[str]
    ) -> AnnualAchievement:
        values = []
        totalDistance = 0.0
        totalDistancePreviousYear = 0.0

        for currentYear in availableYears:
            value = AchievementCalculator.get_total_distance_by_type_and_year(current_user.id, workoutType, currentYear)
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
            color=workoutType.border_color,
            title=gettext('Total Distance'),
            description=__format_distance(totalDistance),
            difference_to_previous_year=__format_distance(abs(totalDistanceDifference)),
            difference_type=AnnualAchievementDifferenceType.get_by_difference(totalDistanceDifference),
            all_year_data=totalDistanceAllYearData,
            unit='km',
            historyItems=[],
        )

    def __create_achievement_total_duration(
        availableYears: list[int], workoutType: WorkoutType, year: int, yearNames: list[str]
    ) -> AnnualAchievement:
        values = []
        totalDuration = 0
        totalDurationPreviousYear = 0

        for currentYear in availableYears:
            value = AchievementCalculator.get_total_duration_by_type_and_year(current_user.id, workoutType, currentYear)
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
            color=workoutType.border_color,
            title=gettext('Total Duration'),
            description=__format_duration(totalDuration),
            difference_to_previous_year=__format_duration(abs(totalDurationDifference)),
            difference_type=AnnualAchievementDifferenceType.get_by_difference(totalDurationDifference),
            all_year_data=totalDurationAllYearData,
            unit=gettext('Hours'),
            historyItems=[],
        )

    def __create_achievement_workout_count(
        availableYears: list[int],
        workoutType: WorkoutType,
        year: int,
        yearNames: list[str],
        title: str,
        icon: str,
        is_font_awesome_icon: bool,
    ) -> AnnualAchievement:
        values = []
        totalWorkoutCount = 0
        totalWorkoutCountPreviousYear = 0

        for currentYear in availableYears:
            value = AchievementCalculator.get_total_number_of_workouts_by_type_and_year(
                current_user.id, workoutType, currentYear
            )
            values.append(value)
            if currentYear == year:
                totalWorkoutCount = value
            elif currentYear == year - 1:
                totalWorkoutCountPreviousYear = value

        totalWorkoutCountDifference = totalWorkoutCount - totalWorkoutCountPreviousYear
        totalWorkoutCountAllYearData = AllYearData(
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
            color=workoutType.border_color,
            title=title,
            description=str(totalWorkoutCount),
            difference_to_previous_year=str(abs(totalWorkoutCountDifference)),
            difference_type=AnnualAchievementDifferenceType.get_by_difference(totalWorkoutCountDifference),
            all_year_data=totalWorkoutCountAllYearData,
            unit='',
            historyItems=[],
        )

    def __create_achievement_longest_workout(
        availableYears: list[int], workoutType: WorkoutType, year: int, yearNames: list[str]
    ) -> AnnualAchievement:
        values = []
        longestWorkout = 0.0
        longestWorkoutPreviousYear = 0.0

        for currentYear in availableYears:
            value = AchievementCalculator.get_longest_distance_by_type_and_year(
                current_user.id, workoutType, currentYear
            )
            values.append(value)
            if currentYear == year:
                longestWorkout = value
            elif currentYear == year - 1:
                longestWorkoutPreviousYear = value

        longestWorkoutDifference = longestWorkout - longestWorkoutPreviousYear
        longestWorkoutAllYearData = AllYearData(
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
            color=workoutType.border_color,
            title=gettext('Longest Workout'),
            description=__format_distance(longestWorkout),
            difference_to_previous_year=__format_distance(abs(longestWorkoutDifference)),
            difference_type=AnnualAchievementDifferenceType.get_by_difference(longestWorkoutDifference),
            all_year_data=longestWorkoutAllYearData,
            unit='km',
            historyItems=[],
        )

    def __create_achievement_average_speed(
        availableYears: list[int], workoutType: WorkoutType, year: int, yearNames: list[str]
    ) -> AnnualAchievement:
        values = []
        averageSpeed = 0.0
        averageSpeedPreviousYear = 0.0

        for currentYear in availableYears:
            value = AchievementCalculator.get_average_speed_by_type_and_year(current_user.id, workoutType, currentYear)
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
            color=workoutType.border_color,
            title=gettext('Average Speed'),
            description=__format_speed(averageSpeed),
            difference_to_previous_year=__format_speed(abs(averageSpeedDifference)),
            difference_type=AnnualAchievementDifferenceType.get_by_difference(averageSpeedDifference),
            all_year_data=averageSpeedAllYearData,
            unit='km/h',
            historyItems=[],
        )

    def __create_achievement_longest_duration(
        availableYears: list[int], workoutType: WorkoutType, year: int, yearNames: list[str]
    ) -> AnnualAchievement:
        values = []
        longestDuration = 0
        longestDurationPreviousYear = 0

        for currentYear in availableYears:
            value = AchievementCalculator.get_longest_duration_by_type_and_year(
                current_user.id, workoutType, currentYear
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
            color=workoutType.border_color,
            title=gettext('Longest Duration'),
            description=__format_duration(longestDuration),
            difference_to_previous_year=__format_duration(abs(longestDurationDifference)),
            difference_type=AnnualAchievementDifferenceType.get_by_difference(longestDurationDifference),
            all_year_data=longestDurationAllYearData,
            unit='km',
            historyItems=[],
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
