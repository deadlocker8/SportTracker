import logging
from itertools import groupby

from flask import Blueprint, render_template, request
from flask_babel import format_datetime
from flask_login import current_user, login_required
from sqlalchemy import extract, false, or_

from sporttracker import Constants
from sporttracker.db import db
from sporttracker.quickFilter.QuickFilterStateEntity import get_quick_filter_state_by_user
from sporttracker.search.SearchParameters import SearchParameters
from sporttracker.user.ParticipantEntity import Participant, get_participants
from sporttracker.user.UserEntity import User
from sporttracker.workout.distance.DistanceWorkoutEntity import DistanceWorkout
from sporttracker.workout.WorkoutEntity import Workout
from sporttracker.workout.WorkoutModel import DistanceWorkoutModel, FitnessWorkoutModel
from sporttracker.workout.WorkoutService import WorkoutService
from sporttracker.workout.WorkoutType import WorkoutType

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint():
    search = Blueprint('search', __name__, static_folder='static', url_prefix='/search')

    @search.route('/search', methods=['GET'])
    @login_required
    def performSearch():
        searchText = (request.args.get('searchText') or '').strip()

        availableYears = WorkoutService.get_available_years(current_user.id)

        selectedYear = __get_int_arg('year')
        if selectedYear not in availableYears:
            selectedYear = None

        selectedMonth = __get_int_arg('month')
        if selectedMonth is not None and not 1 <= selectedMonth <= 12:
            selectedMonth = None

        distanceMin = __get_distance_arg('distanceMin')
        distanceMax = __get_distance_arg('distanceMax')
        if distanceMin is not None and distanceMax is not None and distanceMin > distanceMax:
            distanceMin, distanceMax = distanceMax, distanceMin

        quickFilterState = get_quick_filter_state_by_user(current_user.id)

        participants = get_participants()
        availableParticipantIds = {participant.id for participant in participants}

        isParticipantFilterActive, rawParticipantIds = __get_selected_participant_ids()
        selectedParticipantIds = [
            int(participantId) for participantId in rawParticipantIds if participantId in availableParticipantIds
        ]

        if isParticipantFilterActive:
            checkedParticipantIds = set(selectedParticipantIds)

            if checkedParticipantIds == availableParticipantIds:
                isParticipantFilterActive = False
                participantFilter: list[int] | None = None
            else:
                participantFilter = selectedParticipantIds
        else:
            checkedParticipantIds = availableParticipantIds
            participantFilter = None

        pageNumberValue = __get_int_arg('pageNumber')
        if pageNumberValue is None:
            pageNumberValue = 1
        pageNumberValue = max(pageNumberValue, 1)

        query = (
            db.select(Workout)
            .join(User, Workout.user_id == User.id)
            .filter(User.username == current_user.username)
            .filter(Workout.name.icontains(searchText))
            .filter(Workout.type.in_(quickFilterState.get_active_workout_types()))
        )

        if selectedYear is not None:
            query = query.filter(extract('year', Workout.start_time) == selectedYear)

        if selectedMonth is not None:
            query = query.filter(extract('month', Workout.start_time) == selectedMonth)

        if participantFilter is not None:
            if not participantFilter:
                query = query.filter(false())
            else:
                query = query.filter(Workout.participants.any(Participant.id.in_(participantFilter)))

        if distanceMin is not None or distanceMax is not None:
            distanceQuery = db.select(DistanceWorkout.id)

            if distanceMin is not None:
                distanceQuery = distanceQuery.filter(DistanceWorkout.distance >= distanceMin)

            if distanceMax is not None:
                distanceQuery = distanceQuery.filter(DistanceWorkout.distance <= distanceMax)

            query = query.filter(
                or_(
                    Workout.id.in_(distanceQuery),
                    Workout.type.in_(WorkoutType.get_fitness_workout_types()),
                )
            )

        pagination = db.paginate(
            query.order_by(Workout.start_time.desc()),
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

        searchParameters = SearchParameters(
            searchText=searchText,
            availableYears=availableYears,
            participants=participants,
            isParticipantFilterActive=isParticipantFilterActive,
            selectedYear=selectedYear,
            selectedMonth=selectedMonth,
            selectedParticipantIds=checkedParticipantIds,
            distanceMin=distanceMin // 1000 if distanceMin is not None else None,
            distanceMax=distanceMax // 1000 if distanceMax is not None else None,
        )

        return render_template(
            'search.jinja2',
            results=resultModelItems,
            pagination=pagination,
            searchText=searchText,
            quickFilterState=quickFilterState,
            searchParameters=searchParameters,
        )

    return search


def __get_int_arg(name: str) -> int | None:
    value = request.args.get(name)
    if value is None or value.strip() == '':
        return None

    try:
        return int(value)
    except ValueError:
        return None


def __get_distance_arg(name: str) -> int | None:
    value = __get_int_arg(name)
    if value is None or value < 0:
        return None

    return value * 1000


def __get_selected_participant_ids() -> tuple[bool, list[int]]:
    isParticipantFilterActive = request.args.get('participantsFilterActive') == '1'

    participantIds = []
    for item in request.args.getlist('participants'):
        try:
            participantIds.append(int(item))
        except ValueError:
            continue

    return isParticipantFilterActive, participantIds
