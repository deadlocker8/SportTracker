import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from flask import Blueprint, render_template, redirect, url_for, abort, request, Response, session
from flask_login import login_required, current_user
from flask_pydantic import validate

from sporttracker.logic import Constants
from sporttracker.logic.GpxService import GpxService
from sporttracker.logic.PlannedTourFilterState import (
    get_planned_tour_filter_state_from_session,
    PlannedTourFilterState,
)
from sporttracker.logic.QuickFilterState import get_quick_filter_state_from_session
from sporttracker.logic.model.DistanceWorkout import (
    DistanceWorkout,
)
from sporttracker.logic.model.GpxMetadata import GpxMetadata
from sporttracker.logic.model.LongDistanceTour import (
    LongDistanceTourPlannedTourAssociation,
    get_long_distance_tour_by_id,
)
from sporttracker.logic.model.PlannedTour import (
    PlannedTour,
    TravelType,
    TravelDirection,
    get_planned_tours_filtered,
)
from sporttracker.logic.model.User import (
    User,
    get_all_users_except_self_and_admin,
    get_user_by_id,
)
from sporttracker.logic.model.WorkoutType import WorkoutType
from sporttracker.logic.model.db import db
from sporttracker.logic.service.PlannedTourService import (
    PlannedTourFormModel,
    PlannedTourEditFormModel,
    PlannedTourService,
)

LOGGER = logging.getLogger(Constants.APP_NAME)


@dataclass
class SharedUserModel:
    id: int
    name: str


@dataclass
class LinkedWorkout:
    id: int
    startTime: datetime
    distance: float
    duration: int
    elevation_sum: int


@dataclass
class PlannedTourModel:
    id: int
    name: str
    creationDate: datetime
    lastEditDate: datetime
    type: WorkoutType
    gpxMetadata: GpxMetadata | None
    sharedUsers: list[str]
    ownerId: str
    ownerName: str
    arrivalMethod: TravelType
    departureMethod: TravelType
    direction: TravelDirection
    share_code: str | None
    linkedWorkouts: list[LinkedWorkout]

    @staticmethod
    def __get_linked_workouts_by_planned_tour(plannedTour: PlannedTour) -> list[LinkedWorkout]:
        linkedWorkout = (
            DistanceWorkout.query.filter(DistanceWorkout.user_id == current_user.id)
            .filter(DistanceWorkout.planned_tour == plannedTour)
            .order_by(DistanceWorkout.start_time.asc())
            .all()
        )

        if linkedWorkout is None:
            return []

        result = []
        for workout in linkedWorkout:
            result.append(
                LinkedWorkout(
                    int(workout.id), workout.start_time, workout.distance, workout.duration, workout.elevation_sum
                )
            )

        return result

    @staticmethod
    def create_from_tour(
        plannedTour: PlannedTour,
        includeLinkedWorkouts: bool,
    ) -> 'PlannedTourModel':
        gpxMetadata = plannedTour.get_gpx_metadata()

        linkedWorkouts = []
        if includeLinkedWorkouts:
            linkedWorkouts = PlannedTourModel.__get_linked_workouts_by_planned_tour(plannedTour)

        return PlannedTourModel(
            id=plannedTour.id,
            name=plannedTour.name,  # type: ignore[arg-type]
            creationDate=plannedTour.creation_date,  # type: ignore[arg-type]
            lastEditDate=plannedTour.last_edit_date,  # type: ignore[arg-type]
            type=plannedTour.type,
            gpxMetadata=gpxMetadata,
            sharedUsers=[str(user.id) for user in plannedTour.shared_users],
            ownerId=str(plannedTour.user_id),
            ownerName=get_user_by_id(plannedTour.user_id).username,
            arrivalMethod=plannedTour.arrival_method,
            departureMethod=plannedTour.departure_method,
            direction=plannedTour.direction,
            share_code=plannedTour.share_code,
            linkedWorkouts=linkedWorkouts,
        )


def construct_blueprint(
    gpxService: GpxService,
    gpxPreviewImageSettings: dict[str, Any],
    plannedTourService: PlannedTourService,
) -> Blueprint:
    plannedTours = Blueprint('plannedTours', __name__, static_folder='static', url_prefix='/plannedTours')

    @plannedTours.route('/')
    @login_required
    def listPlannedTours():
        quickFilterState = get_quick_filter_state_from_session()
        plannedTourFilterState = get_planned_tour_filter_state_from_session()

        tours = get_planned_tours_filtered(quickFilterState.get_active_distance_workout_types(), plannedTourFilterState)

        plannedTourList: list[PlannedTourModel] = []
        for tour in tours:
            plannedTourList.append(PlannedTourModel.create_from_tour(tour, True))

        return render_template(
            'plannedTours/plannedTours.jinja2',
            plannedTours=plannedTourList,
            quickFilterState=quickFilterState,
            isGpxPreviewImagesEnabled=gpxPreviewImageSettings['enabled'],
            plannedTourFilterState=plannedTourFilterState,
        )

    @plannedTours.route('/add')
    @login_required
    def add():
        return render_template(
            'plannedTours/plannedTourForm.jinja2',
            users=__get_user_models(get_all_users_except_self_and_admin()),
        )

    @plannedTours.route('/post', methods=['POST'])
    @login_required
    @validate()
    def addPost(form: PlannedTourFormModel):
        shared_user_ids = [int(item) for item in request.form.getlist('sharedUsers')]

        plannedTourService.add_planned_tour(
            form_model=form,
            files=request.files,
            shared_user_ids=shared_user_ids,
            user_id=current_user.id,
        )

        return redirect(url_for('plannedTours.listPlannedTours'))

    @plannedTours.route('/edit/<int:tour_id>')
    @login_required
    def edit(tour_id: int):
        plannedTour = plannedTourService.get_planned_tour_by_id(tour_id)

        if plannedTour is None:
            abort(404)

        gpxFileName = None
        gpxMetadata = plannedTour.get_gpx_metadata()
        if gpxMetadata is not None:
            gpxFileName = gpxMetadata.gpx_file_name

        tourModel = PlannedTourEditFormModel(
            name=plannedTour.name,  # type: ignore[arg-type]
            type=plannedTour.type,
            arrivalMethod=plannedTour.arrival_method,
            departureMethod=plannedTour.departure_method,
            direction=plannedTour.direction,
            ownerId=str(plannedTour.user_id),
            ownerName=get_user_by_id(plannedTour.user_id).username,
            sharedUsers=[str(user.id) for user in plannedTour.shared_users],
            share_code=plannedTour.share_code,
            gpxFileName=gpxFileName,
            hasFitFile=gpxService.has_fit_file(gpxFileName),
        )

        longDistanceTours = LongDistanceTourPlannedTourAssociation.query.filter(
            LongDistanceTourPlannedTourAssociation.planned_tour_id == tour_id
        ).all()

        userIdsForSharedLongDistanceTour = set()
        for longDistanceTourAssociation in longDistanceTours:
            longDistanceTour = get_long_distance_tour_by_id(longDistanceTourAssociation.long_distance_tour_id)
            if longDistanceTour is None:
                continue

            for user in longDistanceTour.shared_users:
                userIdsForSharedLongDistanceTour.add(user.id)

        return render_template(
            'plannedTours/plannedTourForm.jinja2',
            plannedTour=tourModel,
            tour_id=tour_id,
            users=__get_user_models(get_all_users_except_self_and_admin()),
            userIdsForSharedLongDistanceTour=list(userIdsForSharedLongDistanceTour),
        )

    @plannedTours.route('/edit/<int:tour_id>', methods=['POST'])
    @login_required
    @validate()
    def editPost(tour_id: int, form: PlannedTourFormModel):
        try:
            shared_user_ids = [int(item) for item in request.form.getlist('sharedUsers')]

            plannedTourService.edit_planned_tour(
                tour_id=tour_id,
                form_model=form,
                files=request.files,
                shared_user_ids=shared_user_ids,
                user_id=current_user.id,
            )

            return redirect(url_for('plannedTours.listPlannedTours'))
        except ValueError:
            abort(404)

    @plannedTours.route('/delete/<int:tour_id>')
    @login_required
    def delete(tour_id: int):
        try:
            plannedTourService.delete_planned_tour_by_id(tour_id, current_user.id)
            return redirect(url_for('plannedTours.listPlannedTours'))
        except ValueError:
            abort(404)

    @plannedTours.route('/setLastViewedDate')
    @login_required
    def set_last_viewed_date():
        user = User.query.filter(User.id == current_user.id).first()
        user.planned_tours_last_viewed_date = datetime.now()
        db.session.commit()

        return Response(status=204)

    @plannedTours.route('/createShareCode')
    @login_required
    def createShareCode():
        shareCode = uuid.uuid4().hex
        return {
            'url': url_for('maps.showSharedPlannedTour', shareCode=shareCode, _external=True),
            'shareCode': shareCode,
        }

    @plannedTours.route('/applyFilter', methods=['POST'])
    @login_required
    def applyFilter():
        selectedArrivalMethods = [
            TravelType(value)  # type: ignore[call-arg]
            for key, value in request.form.items()
            if key.startswith('plannedTourFilterArrivalMethod')
        ]
        arrivalMethods = {t: t in selectedArrivalMethods for t in TravelType}

        selectedDepartureMethods = [
            TravelType(value)  # type: ignore[call-arg]
            for key, value in request.form.items()
            if key.startswith('plannedTourFilterDepartureMethod')
        ]
        departureMethods = {t: t in selectedDepartureMethods for t in TravelType}

        selectedDirections = [
            TravelDirection(value)  # type: ignore[call-arg]
            for key, value in request.form.items()
            if key.startswith('plannedTourFilterDirection')
        ]
        directions = {t: t in selectedDirections for t in TravelDirection}

        minimumDistanceValue = request.form.get('plannedTourFilterDistanceMin', None)
        minimumDistance = int(minimumDistanceValue) * 1000 if minimumDistanceValue else None

        maximumDistanceValue = request.form.get('plannedTourFilterDistanceMax', None)
        maximumDistance = int(maximumDistanceValue) * 1000 if maximumDistanceValue else None

        plannedTourFilterState = get_planned_tour_filter_state_from_session()
        plannedTourFilterState.update(
            request.form.get('plannedTourFilterStatusDone', 'off').strip().lower() == 'on',
            request.form.get('plannedTourFilterStatusTodo', 'off').strip().lower() == 'on',
            arrivalMethods,
            departureMethods,
            directions,
            request.form.get('plannedTourFilterName', None),
            minimumDistance,
            maximumDistance,
            request.form.get('plannedTourFilterLongDistanceToursInclude', 'off').strip().lower() == 'on',
            request.form.get('plannedTourFilterLongDistanceToursExclude', 'off').strip().lower() == 'on',
        )
        session['plannedTourFilterState'] = plannedTourFilterState.to_json()

        return redirect(url_for('plannedTours.listPlannedTours'))

    @plannedTours.route('/resetFilter')
    @login_required
    def resetFilter():
        session['plannedTourFilterState'] = PlannedTourFilterState().to_json()
        return redirect(url_for('plannedTours.listPlannedTours'))

    return plannedTours


def __get_user_models(users: list[User]) -> list[SharedUserModel]:
    sharedUserModels = []
    for user in users:
        sharedUserModels.append(SharedUserModel(user.id, user.username))
    return sharedUserModels
