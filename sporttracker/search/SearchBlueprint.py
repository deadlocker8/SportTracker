import logging
from itertools import groupby

from flask import Blueprint, render_template, request
from flask_babel import format_datetime
from flask_login import login_required, current_user

from sporttracker.workout.WorkoutBlueprint import DistanceWorkoutModel, FitnessWorkoutModel
from sporttracker import Constants
from sporttracker.workout.WorkoutEntity import Workout
from sporttracker.workout.WorkoutType import WorkoutType
from sporttracker.user.UserEntity import User
from sporttracker.db import db
from sporttracker.quickFilter.QuickFilterStateEntity import get_quick_filter_state_by_user

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint():
    search = Blueprint('search', __name__, static_folder='static', url_prefix='/search')

    @search.route('/search')
    @login_required
    def performSearch():
        searchText = request.args.get('searchText')
        pageNumber = request.args.get('pageNumber')

        quickFilterState = get_quick_filter_state_by_user(current_user.id)

        if searchText is None:
            return render_template(
                'search.jinja2',
                results={},
                quickFilterState=quickFilterState,
            )

        searchText = searchText.strip()

        try:
            pageNumberValue = int(pageNumber)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            pageNumberValue = 1

        if pageNumberValue < 1:
            pageNumberValue = 1

        pagination = db.paginate(
            Workout.query.join(User)
            .filter(User.username == current_user.username)
            .filter(Workout.name.icontains(searchText))
            .filter(Workout.type.in_(quickFilterState.get_active_workout_types()))
            .order_by(Workout.start_time.desc()),
            per_page=10,
            page=pageNumberValue,
        )

        results = {
            k: list(g)
            for k, g in groupby(
                pagination.items,
                key=lambda workout: format_datetime(workout.start_time, format='MMMM yyyy'),
            )
        }

        resultModelItems = {}
        for month, workouts in results.items():
            itemsPerMonth: list[DistanceWorkoutModel | FitnessWorkoutModel] = []

            for workout in workouts:
                if workout.type in WorkoutType.get_distance_workout_types():
                    itemsPerMonth.append(DistanceWorkoutModel.create_from_workout(workout))
                elif workout.type in WorkoutType.get_fitness_workout_types():
                    itemsPerMonth.append(FitnessWorkoutModel.create_from_workout(workout))

            resultModelItems[month] = itemsPerMonth

        return render_template(
            'search.jinja2',
            results=resultModelItems,
            pagination=pagination,
            searchText=searchText,
            quickFilterState=quickFilterState,
        )

    return search
