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
from sporttracker.logic.QuickFilterState import get_quick_filter_state_from_session
from sporttracker.logic.model.LongDistanceTour import (
    LongDistanceTour,
    get_long_distance_tour_by_id,
    get_long_distance_tours,
)
from sporttracker.logic.model.User import User, get_user_by_id, get_all_users_except_self_and_admin, get_users_by_ids
from sporttracker.logic.model.WorkoutType import WorkoutType
from sporttracker.logic.model.db import db

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
                PlannedTourModel.create_from_tour(p, False) for p in longDistanceTour.linked_planned_tours
            ],
        )


class LongDistanceTourFormModel(BaseModel):
    name: str
    type: str
    sharedUsers: list[str] | str | None = None


class LongDistanceTourEditFormModel(BaseModel):
    name: str
    type: str
    ownerId: str
    ownerName: str
    sharedUsers: list[str] | str | None = None


def construct_blueprint(gpxService: GpxService, gpxPreviewImageSettings: dict[str, Any]) -> Blueprint:
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
        )

        return render_template(
            'longDistanceTours/longDistanceTourForm.jinja2',
            longDistanceTour=tourModel,
            tour_id=tour_id,
            users=__get_user_models(get_all_users_except_self_and_admin()),
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

        LOGGER.debug(f'Updated long-distance tour: {longDistanceTour}')
        db.session.commit()

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
