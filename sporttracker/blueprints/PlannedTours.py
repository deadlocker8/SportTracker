import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from flask import Blueprint, render_template, redirect, url_for, abort, request, Response, session
from flask_login import login_required, current_user
from flask_pydantic import validate
from pydantic import BaseModel

from sporttracker.logic import Constants
from sporttracker.logic.GpxService import GpxService
from sporttracker.logic.PlannedTourFilterState import (
    get_planned_tour_filter_state_from_session,
    PlannedTourFilterState,
)
from sporttracker.logic.QuickFilterState import get_quick_filter_state_from_session
from sporttracker.logic.model.DistanceWorkout import (
    DistanceWorkout,
    get_distance_workout_ids_by_planned_tour,
)
from sporttracker.logic.model.GpxMetadata import GpxMetadata
from sporttracker.logic.model.PlannedTour import (
    PlannedTour,
    get_planned_tour_by_id,
    TravelType,
    TravelDirection,
    get_planned_tours_filtered,
)
from sporttracker.logic.model.User import (
    get_users_by_ids,
    User,
    get_all_users_except_self_and_admin,
    get_user_by_id,
)
from sporttracker.logic.model.WorkoutType import WorkoutType
from sporttracker.logic.model.db import db

LOGGER = logging.getLogger(Constants.APP_NAME)


@dataclass
class SharedUserModel:
    id: int
    name: str


@dataclass
class LinkedWorkout:
    id: int
    startTime: datetime


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
            result.append(LinkedWorkout(int(workout.id), workout.start_time))

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


class PlannedTourFormModel(BaseModel):
    name: str
    type: str
    arrivalMethod: str
    departureMethod: str
    direction: str
    sharedUsers: list[str] | str | None = None
    share_code: str | None = None


class PlannedTourEditFormModel(BaseModel):
    name: str
    type: str
    arrivalMethod: TravelType
    departureMethod: TravelType
    direction: TravelDirection
    ownerId: str
    ownerName: str
    sharedUsers: list[str] | str | None = None
    share_code: str | None = None
    gpxFileName: str | None = None
    hasFitFile: bool = False


def construct_blueprint(
    gpxService: GpxService, gpxPreviewImageSettings: dict[str, Any]
) -> Blueprint:
    plannedTours = Blueprint(
        'plannedTours', __name__, static_folder='static', url_prefix='/plannedTours'
    )

    @plannedTours.route('/')
    @login_required
    def listPlannedTours():
        quickFilterState = get_quick_filter_state_from_session()
        plannedTourFilterState = get_planned_tour_filter_state_from_session()

        tours = get_planned_tours_filtered(
            quickFilterState.get_active_distance_workout_types(), plannedTourFilterState
        )

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
        gpxMetadataId = gpxService.handle_gpx_upload_for_planned_tour(
            request.files, gpxPreviewImageSettings
        )
        sharedUserIds = [int(item) for item in request.form.getlist('sharedUsers')]
        sharedUsers = get_users_by_ids(sharedUserIds)

        plannedTour = PlannedTour(
            name=form.name,
            type=WorkoutType(form.type),  # type: ignore[call-arg]
            user_id=current_user.id,
            creation_date=datetime.now(),
            last_edit_date=datetime.now(),
            last_edit_user_id=current_user.id,
            gpx_metadata_id=gpxMetadataId,
            shared_users=sharedUsers,
            arrival_method=TravelType(form.arrivalMethod),  # type: ignore[call-arg]
            departure_method=TravelType(form.departureMethod),  # type: ignore[call-arg]
            direction=TravelDirection(form.direction),  # type: ignore[call-arg]
            share_code=form.share_code,
        )

        LOGGER.debug(f'Saved new planned tour: {plannedTour}')
        db.session.add(plannedTour)
        db.session.commit()

        return redirect(url_for('plannedTours.listPlannedTours'))

    @plannedTours.route('/edit/<int:tour_id>')
    @login_required
    def edit(tour_id: int):
        plannedTour = get_planned_tour_by_id(tour_id)

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

        return render_template(
            'plannedTours/plannedTourForm.jinja2',
            plannedTour=tourModel,
            tour_id=tour_id,
            users=__get_user_models(get_all_users_except_self_and_admin()),
        )

    @plannedTours.route('/edit/<int:tour_id>', methods=['POST'])
    @login_required
    @validate()
    def editPost(tour_id: int, form: PlannedTourFormModel):
        plannedTour = get_planned_tour_by_id(tour_id)

        if plannedTour is None:
            abort(404)

        plannedTour.type = WorkoutType(form.type)  # type: ignore[call-arg]
        plannedTour.name = form.name  # type: ignore[assignment]
        plannedTour.last_edit_date = datetime.now()  # type: ignore[assignment]
        plannedTour.last_edit_user_id = current_user.id
        plannedTour.arrival_method = TravelType(form.arrivalMethod)  # type: ignore[call-arg]
        plannedTour.departure_method = TravelType(form.departureMethod)  # type: ignore[call-arg]
        plannedTour.direction = TravelDirection(form.direction)  # type: ignore[call-arg]
        plannedTour.share_code = form.share_code if form.share_code else None  # type: ignore[assignment]

        newGpxMetadataId = gpxService.handle_gpx_upload_for_planned_tour(
            request.files, gpxPreviewImageSettings
        )
        if plannedTour.gpx_metadata_id is None:
            plannedTour.gpx_metadata_id = newGpxMetadataId
        else:
            if newGpxMetadataId is not None:
                gpxService.delete_gpx(plannedTour, current_user.id)
                plannedTour.gpx_metadata_id = newGpxMetadataId

        sharedUserIds = [int(item) for item in request.form.getlist('sharedUsers')]
        sharedUsers = get_users_by_ids(sharedUserIds)
        plannedTour.shared_users = sharedUsers

        # The list of shared users may have changed.
        # All workouts that link to this planned tour must be checked, whether they are owned by the owner of the
        # planned tour or if the planned tour is still shared to the owner of the workout.
        linkedIds = get_distance_workout_ids_by_planned_tour(plannedTour)
        for workoutId in linkedIds:
            workout = DistanceWorkout.query.filter().filter(DistanceWorkout.id == workoutId).first()
            if workout.user_id == plannedTour.user_id:
                continue

            if workout.user_id in sharedUserIds:
                continue

            workout.planned_tour = None
            LOGGER.debug(f'Removed linked planned tour from workout: {workoutId}')
            db.session.commit()

        LOGGER.debug(f'Updated planned tour: {plannedTour}')
        db.session.commit()

        return redirect(url_for('plannedTours.listPlannedTours'))

    @plannedTours.route('/delete/<int:tour_id>')
    @login_required
    def delete(tour_id: int):
        plannedTour = get_planned_tour_by_id(tour_id)

        if plannedTour is None:
            abort(404)

        if current_user.id != plannedTour.user_id:
            abort(403)

        gpxService.delete_gpx(plannedTour, current_user.id)

        linkedIds = get_distance_workout_ids_by_planned_tour(plannedTour)
        for workoutId in linkedIds:
            workout = DistanceWorkout.query.filter().filter(DistanceWorkout.id == workoutId).first()
            workout.planned_tour = None
            LOGGER.debug(f'Removed linked planned tour from workout: {workoutId}')
            db.session.commit()

        LOGGER.debug(f'Deleted planned tour: {plannedTour}')
        db.session.delete(plannedTour)
        db.session.commit()

        return redirect(url_for('plannedTours.listPlannedTours'))

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
