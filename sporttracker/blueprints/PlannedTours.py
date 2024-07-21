import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from flask import Blueprint, render_template, redirect, url_for, abort, request, Response
from flask_login import login_required, current_user
from flask_pydantic import validate
from pydantic import BaseModel
from sqlalchemy.sql import or_

from sporttracker.blueprints.GpxTracks import handleGpxTrackForPlannedTour
from sporttracker.logic import Constants
from sporttracker.logic.GpxService import GpxService, GpxMetaInfo
from sporttracker.logic.QuickFilterState import get_quick_filter_state_from_session
from sporttracker.logic.model.PlannedTour import (
    PlannedTour,
    get_planned_tour_by_id,
    TravelType,
    TravelDirection,
)
from sporttracker.logic.model.Track import TrackType
from sporttracker.logic.model.User import (
    get_users_by_ids,
    User,
    get_all_users_except_self_and_admin,
    get_user_by_id,
)
from sporttracker.logic.model.db import db

LOGGER = logging.getLogger(Constants.APP_NAME)


@dataclass
class SharedUserModel:
    id: int
    name: str


@dataclass
class PlannedTourModel:
    id: int
    name: str
    creationDate: datetime
    lastEditDate: datetime
    type: TrackType
    gpxFileName: str
    gpxMetaInfo: GpxMetaInfo | None
    sharedUsers: list[str]
    ownerId: str
    ownerName: str
    arrivalMethod: TravelType
    departureMethod: TravelType
    direction: TravelDirection


class PlannedTourFormModel(BaseModel):
    name: str
    type: str
    arrivalMethod: str
    departureMethod: str
    direction: str
    sharedUsers: list[str] | str | None = None


def construct_blueprint(uploadFolder: str, gpxPreviewImageSettings: dict[str, Any]):
    plannedTours = Blueprint(
        'plannedTours', __name__, static_folder='static', url_prefix='/plannedTours'
    )

    @plannedTours.route('/')
    @login_required
    def listPlannedTours():
        quickFilterState = get_quick_filter_state_from_session()

        tours: list[PlannedTour] = (
            PlannedTour.query.filter(
                or_(
                    PlannedTour.user_id == current_user.id,
                    PlannedTour.shared_users.any(id=current_user.id),
                )
            )
            .filter(PlannedTour.type.in_(quickFilterState.get_active_types()))
            .order_by(PlannedTour.name.asc())
            .all()
        )

        plannedTourList: list[PlannedTourModel] = []
        for tour in tours:
            if tour.gpxFileName is None:
                gpxMetaInfo = None
            else:
                gpxTrackPath = os.path.join(uploadFolder, str(tour.gpxFileName))
                gpxService = GpxService(gpxTrackPath)
                gpxMetaInfo = gpxService.get_meta_info()

            plannedTourList.append(
                PlannedTourModel(
                    id=tour.id,
                    name=tour.name,  # type: ignore[arg-type]
                    creationDate=tour.creation_date,  # type: ignore[arg-type]
                    lastEditDate=tour.last_edit_date,  # type: ignore[arg-type]
                    type=tour.type,
                    gpxFileName=tour.gpxFileName,
                    gpxMetaInfo=gpxMetaInfo,
                    sharedUsers=[str(user.id) for user in tour.shared_users],
                    ownerId=str(tour.user_id),
                    ownerName=get_user_by_id(tour.user_id).username,
                    arrivalMethod=tour.arrival_method,
                    departureMethod=tour.departure_method,
                    direction=tour.direction,
                )
            )

        return render_template(
            'plannedTours/plannedTours.jinja2',
            plannedTours=plannedTourList,
            quickFilterState=quickFilterState,
            isGpxPreviewImagesEnabled=gpxPreviewImageSettings['enabled'],
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
        gpxFileName = handleGpxTrackForPlannedTour(
            request.files, uploadFolder, gpxPreviewImageSettings
        )

        sharedUserIds = [int(item) for item in request.form.getlist('sharedUsers')]
        sharedUsers = get_users_by_ids(sharedUserIds)

        plannedTour = PlannedTour(
            name=form.name,
            type=TrackType(form.type),  # type: ignore[call-arg]
            user_id=current_user.id,
            creation_date=datetime.now(),
            last_edit_date=datetime.now(),
            last_edit_user_id=current_user.id,
            gpxFileName=gpxFileName,
            shared_users=sharedUsers,
            arrival_method=TravelType(form.arrivalMethod),  # type: ignore[call-arg]
            departure_method=TravelType(form.departureMethod),  # type: ignore[call-arg]
            direction=TravelDirection(form.direction),  # type: ignore[call-arg]
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

        tourModel = PlannedTourModel(
            id=plannedTour.id,
            name=plannedTour.name,  # type: ignore[arg-type]
            creationDate=plannedTour.creation_date,  # type: ignore[arg-type]
            lastEditDate=plannedTour.last_edit_date,  # type: ignore[arg-type]
            type=plannedTour.type,
            gpxFileName=plannedTour.gpxFileName,
            gpxMetaInfo=None,
            sharedUsers=[str(user.id) for user in plannedTour.shared_users],
            ownerId=str(plannedTour.user_id),
            ownerName=get_user_by_id(plannedTour.user_id).username,
            arrivalMethod=plannedTour.arrival_method,
            departureMethod=plannedTour.departure_method,
            direction=plannedTour.direction,
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

        plannedTour.type = TrackType(form.type)  # type: ignore[call-arg]
        plannedTour.name = form.name  # type: ignore[assignment]
        plannedTour.last_edit_date = datetime.now()  # type: ignore[assignment]
        plannedTour.last_edit_user_id = current_user.id
        plannedTour.arrival_method = TravelType(form.arrivalMethod)  # type: ignore[call-arg]
        plannedTour.departure_method = TravelType(form.departureMethod)  # type: ignore[call-arg]
        plannedTour.direction = TravelDirection(form.direction)  # type: ignore[call-arg]

        newGpxFileName = handleGpxTrackForPlannedTour(
            request.files, uploadFolder, gpxPreviewImageSettings
        )
        if plannedTour.gpxFileName is None:
            plannedTour.gpxFileName = newGpxFileName
        else:
            if newGpxFileName is not None:
                plannedTour.gpxFileName = newGpxFileName

        sharedUserIds = [int(item) for item in request.form.getlist('sharedUsers')]
        sharedUsers = get_users_by_ids(sharedUserIds)
        plannedTour.shared_users = sharedUsers

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

        if plannedTour.gpxFileName is not None:
            try:
                os.remove(os.path.join(uploadFolder, plannedTour.gpxFileName))
                LOGGER.debug(
                    f'Deleted linked gpx file "{plannedTour.gpxFileName}" for planned tour with id {tour_id}'
                )
            except OSError as e:
                LOGGER.error(e)

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

    return plannedTours


def __get_user_models(users: list[User]) -> list[SharedUserModel]:
    sharedUserModels = []
    for user in users:
        sharedUserModels.append(SharedUserModel(user.id, user.username))
    return sharedUserModels
