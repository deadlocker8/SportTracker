import logging
from datetime import datetime

from flask import Blueprint, render_template
from flask_babel import gettext
from flask_login import login_required

from sporttracker.helpers import Helpers
from sporttracker.logic import Constants
from sporttracker.logic.AchievementCalculator import AchievementCalculator
from sporttracker.logic.model.Achievement import (
    Achievement,
    LongestWorkoutDistanceAchievementHistoryItem,
    LongestWorkoutDurationAchievementHistoryItem,
)
from sporttracker.workout.WorkoutType import WorkoutType

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint():
    achievements = Blueprint('achievements', __name__, static_folder='static', url_prefix='/achievements')

    @achievements.route('/')
    @login_required
    def showAchievements():
        return render_template('achievements.jinja2', achievements=__get_achievements())

    def __get_achievements() -> dict[WorkoutType, list[Achievement]]:
        result = {}

        for workoutType in WorkoutType.get_distance_workout_types():
            achievementList = __create_distance_based_achievements(workoutType)
            result[workoutType] = achievementList

        for workoutType in WorkoutType.get_fitness_workout_types():
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
                historyItems=[],
            )
        )

        longestWorkout = LongestWorkoutDistanceAchievementHistoryItem.get_dummy_instance()
        longestWorkouts = AchievementCalculator.get_workouts_with_longest_distances_by_type(workoutType)
        if longestWorkouts:
            longestWorkout = longestWorkouts[0]

        achievementList.append(
            Achievement(
                icon='route',
                is_font_awesome_icon=False,
                is_outlined_icon=False,
                color=workoutType.border_color,
                title=gettext('Longest Workout'),
                description=gettext(
                    'You completed <span class="fw-bold">{longestWorkoutDistance}</span> in one trip on <span class="fw-bold">{longestWorkoutDate}</span>!'
                ).format(
                    longestWorkoutDistance=longestWorkout.get_value_formatted(),
                    longestWorkoutDate=longestWorkout.get_date_formatted()
                    if longestWorkout.get_link() is None
                    else longestWorkout.get_link(),
                ),
                historyItems=longestWorkouts,
            )
        )

        achievementList.append(
            Achievement(
                icon='map',
                is_font_awesome_icon=False,
                is_outlined_icon=False,
                color=workoutType.border_color,
                title=gettext('Total Distance'),
                description=gettext('You completed a total of <span class="fw-bold">{totalDistance} km</span>!').format(
                    totalDistance=Helpers.format_decimal(
                        AchievementCalculator.get_total_distance_by_type(workoutType), decimals=2
                    )
                ),
                historyItems=[],
            )
        )

        bestMonths = AchievementCalculator.get_best_distance_months_by_type(workoutType)
        achievementList.append(
            Achievement(
                icon='calendar_month',
                is_font_awesome_icon=False,
                is_outlined_icon=False,
                color=workoutType.border_color,
                title=gettext('Best Month'),
                description=gettext(
                    '<span class="fw-bold">{bestMonthName}</span> was your best month with <span class="fw-bold">'
                    '{bestMonthDistance}</span>!'
                ).format(
                    bestMonthName=bestMonths[0].get_date_formatted(),
                    bestMonthDistance=bestMonths[0].get_value_formatted(),
                ),
                historyItems=bestMonths,
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
                historyItems=[],
            )
        )

        longestWorkout = LongestWorkoutDurationAchievementHistoryItem.get_dummy_instance()
        longestWorkouts = AchievementCalculator.get_workouts_with_longest_durations_by_type(workoutType)
        if longestWorkouts:
            longestWorkout = longestWorkouts[0]

        achievementList.append(
            Achievement(
                icon='schedule',
                is_font_awesome_icon=False,
                is_outlined_icon=False,
                color=workoutType.border_color,
                title=gettext('Longest Duration'),
                description=gettext(
                    'You completed <span class="fw-bold">{longestDuration}</span> in one workout on <span class="fw-bold">{longestDurationDate}</span>!'
                ).format(
                    longestDuration=longestWorkout.get_value_formatted(),
                    longestDurationDate=longestWorkout.get_date_formatted()
                    if longestWorkout.get_link() is None
                    else longestWorkout.get_link(),
                ),
                historyItems=longestWorkouts,
            )
        )

        achievementList.append(
            Achievement(
                icon='timer',
                is_font_awesome_icon=False,
                is_outlined_icon=True,
                color=workoutType.border_color,
                title=gettext('Total Duration'),
                description=gettext('You completed a total of <span class="fw-bold">{totalDuration} h</span>!').format(
                    totalDuration=Helpers.format_duration(AchievementCalculator.get_total_duration_by_type(workoutType))
                ),
                historyItems=[],
            )
        )

        bestMonths = AchievementCalculator.get_best_duration_month_by_type(workoutType)
        achievementList.append(
            Achievement(
                icon='calendar_month',
                is_font_awesome_icon=False,
                is_outlined_icon=False,
                color=workoutType.border_color,
                title=gettext('Best Month'),
                description=gettext(
                    '<span class="fw-bold">{bestMonthName}</span> was your best month with <span class="fw-bold">'
                    '{bestMonthDuration}</span>!'
                ).format(
                    bestMonthName=bestMonths[0].get_date_formatted(),
                    bestMonthDuration=bestMonths[0].get_value_formatted(),
                ),
                historyItems=bestMonths,
            )
        )

        return achievementList

    return achievements
