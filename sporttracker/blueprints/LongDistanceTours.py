import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from flask import Blueprint, render_template, Response, request, redirect, url_for, abort
from flask_login import login_required, current_user
from flask_pydantic import validate
from pydantic import BaseModel

from sporttracker.blueprints.PlannedTours import PlannedTourModel, __get_user_models
from sporttracker.logic import Constants
from sporttracker.logic.GpxService import GpxService
from sporttracker.logic.QuickFilterState import get_quick_filter_state_from_session, QuickFilterState
from sporttracker.logic.model.LongDistanceTour import (
    LongDistanceTour,
    get_long_distance_tour_by_id,
    get_long_distance_tours,
    LongDistanceTourPlannedTourAssociation,
)
from sporttracker.logic.model.PlannedTour import get_planned_tours
from sporttracker.logic.model.User import User, get_user_by_id, get_all_users_except_self_and_admin, get_users_by_ids
from sporttracker.logic.model.WorkoutType import WorkoutType
from sporttracker.logic.model.db import db
from sporttracker.logic.service.PlannedTourService import PlannedTourService

LOGGER = logging.getLogger(Constants.APP_NAME)


@dataclass
class SharedUserModel:
    id: int
    name: str


@dataclass
class LongDistanceTourModel:
    id: int
    name: str
    creationDate: datetime
    lastEditDate: datetime
    type: WorkoutType
    sharedUsers: list[str]
    ownerId: str
    ownerName: str
    linkedPlannedTours: list[PlannedTourModel]

    @staticmethod
    def create_from_tour(longDistanceTour: LongDistanceTour) -> 'LongDistanceTourModel':
        return LongDistanceTourModel(
            id=longDistanceTour.id,
            name=longDistanceTour.name,  # type: ignore[arg-type]
            creationDate=longDistanceTour.creation_date,  # type: ignore[arg-type]
            lastEditDate=longDistanceTour.last_edit_date,  # type: ignore[arg-type]
            type=longDistanceTour.type,
            sharedUsers=[str(user.id) for user in longDistanceTour.shared_users],
            ownerId=str(longDistanceTour.user_id),
            ownerName=get_user_by_id(longDistanceTour.user_id).username,
            linkedPlannedTours=[
                PlannedTourModel.create_from_tour(
                    PlannedTourService.get_planned_tour_by_id(p.planned_tour_id),  # type: ignore[arg-type]
                    True,
                )
                for p in longDistanceTour.linked_planned_tours
            ],
        )

    def get_number_of_completed_stages(self) -> int:
        return len([t for t in self.linkedPlannedTours if len(t.linkedWorkouts) > 0])

    def get_total_distance(self) -> float:
        totalDistance = 0.0
        for planned_tour in self.linkedPlannedTours:
            if planned_tour.gpxMetadata is not None:
                totalDistance += planned_tour.gpxMetadata.length

        return totalDistance

    def get_completed_distance(self) -> float:
        completedDistance = 0.0
        for planned_tour in self.linkedPlannedTours:
            if planned_tour.gpxMetadata is None:
                continue

            if len(planned_tour.linkedWorkouts) == 0:
                continue

            completedDistance += planned_tour.gpxMetadata.length

        return completedDistance


class LongDistanceTourFormModel(BaseModel):
    name: str
    type: str
    sharedUsers: list[str] | str | None = None
    linkedPlannedTours: list[str] | str | None = None


class LongDistanceTourEditFormModel(BaseModel):
    name: str
    type: str
    ownerId: str
    ownerName: str
    sharedUsers: list[str] | str | None = None
    linkedPlannedTours: list[str] | str | None = None


def construct_blueprint(
    gpxService: GpxService, gpxPreviewImageSettings: dict[str, Any], plannedToursService: PlannedTourService
) -> Blueprint:
    longDistanceTours = Blueprint(
        'longDistanceTours', __name__, static_folder='static', url_prefix='/longDistanceTours'
    )

    @longDistanceTours.route('/')
    @login_required
    def listLongDistanceTours():
        quickFilterState = get_quick_filter_state_from_session()

        longDistanceTourList = get_long_distance_tours(quickFilterState.get_active_distance_workout_types())

        return render_template(
            'longDistanceTours/longDistanceTours.jinja2',
            longDistanceTours=[LongDistanceTourModel.create_from_tour(t) for t in longDistanceTourList],
            quickFilterState=quickFilterState,
            isGpxPreviewImagesEnabled=gpxPreviewImageSettings['enabled'],
        )

    @longDistanceTours.route('/add')
    @login_required
    def add():
        return render_template(
            'longDistanceTours/longDistanceTourForm.jinja2',
            users=__get_user_models(get_all_users_except_self_and_admin()),
            plannedTours=__get_available_planned_tours(get_quick_filter_state_from_session()),
        )

    @longDistanceTours.route('/post', methods=['POST'])
    @login_required
    @validate()
    def addPost(form: LongDistanceTourFormModel):
        sharedUserIds = [int(item) for item in request.form.getlist('sharedUsers')]
        sharedUsers = get_users_by_ids(sharedUserIds)

        longDistanceTour = LongDistanceTour(
            name=form.name,
            type=WorkoutType(form.type),  # type: ignore[call-arg]
            user_id=current_user.id,
            creation_date=datetime.now(),
            last_edit_date=datetime.now(),
            last_edit_user_id=current_user.id,
            shared_users=sharedUsers,
        )

        LOGGER.debug(f'Saved new long-distance tour: {longDistanceTour}')
        db.session.add(longDistanceTour)
        db.session.commit()

        longDistanceTour.linked_planned_tours = __get_linked_planned_tour_associations(longDistanceTour.id)
        db.session.commit()

        return redirect(url_for('longDistanceTours.listLongDistanceTours'))

    @longDistanceTours.route('/edit/<int:tour_id>')
    @login_required
    def edit(tour_id: int):
        longDistanceTour = get_long_distance_tour_by_id(tour_id)

        if longDistanceTour is None:
            abort(404)

        tourModel = LongDistanceTourEditFormModel(
            name=longDistanceTour.name,  # type: ignore[arg-type]
            type=longDistanceTour.type,
            ownerId=str(longDistanceTour.user_id),
            ownerName=get_user_by_id(longDistanceTour.user_id).username,
            sharedUsers=[str(user.id) for user in longDistanceTour.shared_users],
            linkedPlannedTours=[str(p.planned_tour_id) for p in longDistanceTour.linked_planned_tours],
        )

        return render_template(
            'longDistanceTours/longDistanceTourForm.jinja2',
            longDistanceTour=tourModel,
            tour_id=tour_id,
            users=__get_user_models(get_all_users_except_self_and_admin()),
            plannedTours=__get_available_planned_tours(get_quick_filter_state_from_session()),
        )

    @longDistanceTours.route('/edit/<int:tour_id>', methods=['POST'])
    @login_required
    @validate()
    def editPost(tour_id: int, form: LongDistanceTourFormModel):
        longDistanceTour = get_long_distance_tour_by_id(tour_id)

        if longDistanceTour is None:
            abort(404)

        longDistanceTour.type = WorkoutType(form.type)  # type: ignore[call-arg]
        longDistanceTour.name = form.name  # type: ignore[assignment]
        longDistanceTour.last_edit_date = datetime.now()  # type: ignore[assignment]
        longDistanceTour.last_edit_user_id = current_user.id

        sharedUserIds = [int(item) for item in request.form.getlist('sharedUsers')]
        sharedUsers = get_users_by_ids(sharedUserIds)
        longDistanceTour.shared_users = sharedUsers

        longDistanceTour.linked_planned_tours = []
        db.session.commit()
        longDistanceTour.linked_planned_tours = __get_linked_planned_tour_associations(tour_id)
        db.session.commit()

        LOGGER.debug(f'Updated long-distance tour: {longDistanceTour}')

        return redirect(url_for('longDistanceTours.listLongDistanceTours'))

    @longDistanceTours.route('/delete/<int:tour_id>')
    @login_required
    def delete(tour_id: int):
        longDistanceTour = get_long_distance_tour_by_id(tour_id)

        if longDistanceTour is None:
            abort(404)

        if current_user.id != longDistanceTour.user_id:
            abort(403)

        LOGGER.debug(f'Deleted long-distance tour: {longDistanceTour}')
        db.session.delete(longDistanceTour)
        db.session.commit()

        return redirect(url_for('longDistanceTours.listLongDistanceTours'))

    @longDistanceTours.route('/setLastViewedDate')
    @login_required
    def set_last_viewed_date():
        user = User.query.filter(User.id == current_user.id).first()
        user.long_distance_tours_last_viewed_date = datetime.now()
        db.session.commit()

        return Response(status=204)

    return longDistanceTours


def __get_available_planned_tours(quickFilterState: QuickFilterState) -> list[PlannedTourModel]:
    plannedTours = get_planned_tours(quickFilterState.get_active_distance_workout_types())
    return [PlannedTourModel.create_from_tour(t, False) for t in plannedTours]


def __get_linked_planned_tour_associations(tour_id):
    linkedPlannedTourIds = [int(item) for item in request.form.getlist('linkedPlannedTours')]
    linkedPlannedTours = []
    for order, linkedPlannedTourId in enumerate(linkedPlannedTourIds):
        linkedPlannedTours.append(
            LongDistanceTourPlannedTourAssociation(
                long_distance_tour_id=tour_id, planned_tour_id=linkedPlannedTourId, order=order
            )
        )
    return linkedPlannedTours
