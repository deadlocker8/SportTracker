import logging
from datetime import datetime

from flask import Blueprint, render_template, url_for
from flask_babel import gettext, format_datetime
from flask_login import login_required

from sporttracker.helpers import Helpers
from sporttracker.logic import Constants
from sporttracker.logic.AchievementCalculator import AchievementCalculator
from sporttracker.logic.model.Achievement import Achievement
from sporttracker.logic.model.WorkoutType import WorkoutType

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint():
    achievements = Blueprint(
        'achievements', __name__, static_folder='static', url_prefix='/achievements'
    )

    @achievements.route('/')
    @login_required
    def showAchievements():
        return render_template('achievements.jinja2', achievements=__get_achievements())

    def __get_achievements() -> dict[WorkoutType, list[Achievement]]:
        result = {}

        for workoutType in WorkoutType.get_distance_workout_types():
            achievementList = __create_distance_based_achievements(workoutType)
            result[workoutType] = achievementList

        for workoutType in WorkoutType.get_workout_workout_types():
            achievementList = __create_duration_based_achievements(workoutType)
            result[workoutType] = achievementList

        return result

    def __create_distance_based_achievements(workoutType: WorkoutType) -> list[Achievement]:
        achievementList = []
        streak = AchievementCalculator.get_streaks_by_type(workoutType, datetime.now().date())
        achievementList.append(
            Achievement(
                icon='sports_score',
                is_font_awesome_icon=False,
                is_outlined_icon=False,
                color=workoutType.border_color,
                title=gettext('Month Goal Streak'),
                description=gettext(
                    'You have achieved all your monthly goals for <span class="fw-bold">{currentStreak}</span> '
                    'months in a row!<br>(Best: <span class="fw-bold">{maxStreak}</span>)'
                ).format(currentStreak=streak[1], maxStreak=streak[0]),
            )
        )

        longestDistance = 0.0
        longestWorkoutDate = gettext('no date')
        longestWorkout = AchievementCalculator.get_workout_with_longest_distance_by_type(
            workoutType
        )
        if longestWorkout is not None:
            longestDistance = longestWorkout.distance / 1000
            longestWorkoutDate = format_datetime(longestWorkout.start_time, format='dd.MM.yyyy')
            longestWorkoutDate = f'<a href="{url_for("maps.showSingleWorkout", workout_id=longestWorkout.id)}">{longestWorkoutDate}</a>'

        achievementList.append(
            Achievement(
                icon='route',
                is_font_awesome_icon=False,
                is_outlined_icon=False,
                color=workoutType.border_color,
                title=gettext('Longest Workout'),
                description=gettext(
                    'You completed <span class="fw-bold">{longestWorkoutDistance} km</span> in one trip on <span class="fw-bold">{longestWorkoutDate}</span>!'
                ).format(
                    longestWorkoutDistance=Helpers.format_decimal(longestDistance, decimals=2),
                    longestWorkoutDate=longestWorkoutDate,
                ),
            )
        )

        achievementList.append(
            Achievement(
                icon='map',
                is_font_awesome_icon=False,
                is_outlined_icon=False,
                color=workoutType.border_color,
                title=gettext('Total Distance'),
                description=gettext(
                    'You completed a total of <span class="fw-bold">{totalDistance} km</span>!'
                ).format(
                    totalDistance=Helpers.format_decimal(
                        AchievementCalculator.get_total_distance_by_type(workoutType), decimals=2
                    )
                ),
            )
        )

        bestMonth = AchievementCalculator.get_best_distance_month_by_type(workoutType)
        achievementList.append(
            Achievement(
                icon='calendar_month',
                is_font_awesome_icon=False,
                is_outlined_icon=False,
                color=workoutType.border_color,
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

        return achievementList

    def __create_duration_based_achievements(workoutType: WorkoutType) -> list[Achievement]:
        achievementList = []
        streak = AchievementCalculator.get_streaks_by_type(workoutType, datetime.now().date())
        achievementList.append(
            Achievement(
                icon='sports_score',
                is_font_awesome_icon=False,
                is_outlined_icon=False,
                color=workoutType.border_color,
                title=gettext('Month Goal Streak'),
                description=gettext(
                    'You have achieved all your monthly goals for <span class="fw-bold">{currentStreak}</span> '
                    'months in a row!<br>(Best: <span class="fw-bold">{maxStreak}</span>)'
                ).format(currentStreak=streak[1], maxStreak=streak[0]),
            )
        )

        longestDuration = 0
        longestDurationDate = gettext('no date')
        longestWorkout = AchievementCalculator.get_workout_with_longest_duration_by_type(
            workoutType
        )
        if longestWorkout is not None:
            longestDuration = longestWorkout.duration
            longestDurationDate = format_datetime(longestWorkout.start_time, format='dd.MM.yyyy')
            longestDurationDate = f'<a href="{url_for("tracks.edit", workout_id=longestWorkout.id)}">{longestDurationDate}</a>'

        achievementList.append(
            Achievement(
                icon='schedule',
                is_font_awesome_icon=False,
                is_outlined_icon=False,
                color=workoutType.border_color,
                title=gettext('Longest Duration'),
                description=gettext(
                    'You completed <span class="fw-bold">{longestDuration} h </span> in one workout on <span class="fw-bold">{longestDurationDate}</span>!'
                ).format(
                    longestDuration=Helpers.format_duration(longestDuration),
                    longestDurationDate=longestDurationDate,
                ),
            )
        )

        achievementList.append(
            Achievement(
                icon='timer',
                is_font_awesome_icon=False,
                is_outlined_icon=True,
                color=workoutType.border_color,
                title=gettext('Total Duration'),
                description=gettext(
                    'You completed a total of <span class="fw-bold">{totalDuration} h</span>!'
                ).format(
                    totalDuration=Helpers.format_duration(
                        AchievementCalculator.get_total_duration_by_type(workoutType)
                    )
                ),
            )
        )

        bestMonth = AchievementCalculator.get_best_duration_month_by_type(workoutType)
        achievementList.append(
            Achievement(
                icon='calendar_month',
                is_font_awesome_icon=False,
                is_outlined_icon=False,
                color=workoutType.border_color,
                title=gettext('Best Month'),
                description=gettext(
                    '<span class="fw-bold">{bestMonthName}</span> was your best month with <span class="fw-bold">'
                    '{bestMonthDuration} h</span>!'
                ).format(
                    bestMonthName=bestMonth[0],
                    bestMonthDuration=Helpers.format_duration(bestMonth[1]),
                ),
            )
        )

        return achievementList

    return achievements
