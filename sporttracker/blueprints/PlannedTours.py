import logging
import os
from dataclasses import dataclass
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, abort, request
from flask_login import login_required, current_user
from flask_pydantic import validate
from pydantic import BaseModel

from sporttracker.blueprints.GpxTracks import handleGpxTrack
from sporttracker.logic import Constants
from sporttracker.logic.GpxService import GpxService
from sporttracker.logic.QuickFilterState import get_quick_filter_state_from_session
from sporttracker.logic.model.PlannedTour import PlannedTour, get_planned_tour_by_id
from sporttracker.logic.model.Track import TrackType
from sporttracker.logic.model.User import (
    get_users_by_ids,
    User,
    get_all_users_except_self_and_admin,
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
    lastEditDate: datetime
    type: TrackType
    gpxFileName: str
    distance: float | None
    sharedUsers: list[str]


class PlannedTourFormModel(BaseModel):
    name: str
    type: str
    sharedUsers: list[str] | str | None = None


def construct_blueprint(uploadFolder: str):
    plannedTours = Blueprint(
        'plannedTours', __name__, static_folder='static', url_prefix='/plannedTours'
    )

    @plannedTours.route('/')
    @login_required
    def listPlannedTours():
        quickFilterState = get_quick_filter_state_from_session()

        tours: list[PlannedTour] = (
            PlannedTour.query.filter(PlannedTour.user_id == current_user.id)
            .filter(PlannedTour.type.in_(quickFilterState.get_active_types()))
            .order_by(PlannedTour.name.desc())
            .all()
        )

        plannedTourList: list[PlannedTourModel] = []
        for tour in tours:
            if tour.gpxFileName is None:
                distance = None
            else:
                gpxTrackPath = os.path.join(uploadFolder, str(tour.gpxFileName))
                gpxService = GpxService(gpxTrackPath)
                distance = gpxService.get_length()

            plannedTourList.append(
                PlannedTourModel(
                    id=tour.id,
                    name=tour.name,  # type: ignore[arg-type]
                    lastEditDate=tour.last_edit_date,  # type: ignore[arg-type]
                    type=tour.type,
                    gpxFileName=tour.gpxFileName,
                    distance=distance,
                    sharedUsers=[str(user.id) for user in tour.shared_users],
                )
            )

        return render_template(
            'plannedTours/plannedTours.jinja2',
            plannedTours=plannedTourList,
            quickFilterState=quickFilterState,
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
        gpxFileName = handleGpxTrack(request.files, uploadFolder)

        sharedUserIds = [int(item) for item in request.form.getlist('participants')]
        sharedUsers = get_users_by_ids(sharedUserIds)

        plannedTour = PlannedTour(
            name=form.name,
            type=TrackType(form.type),  # type: ignore[call-arg]
            user_id=current_user.id,
            last_edit_date=datetime.now(),
            gpxFileName=gpxFileName,
            shared_users=sharedUsers,
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
            lastEditDate=plannedTour.last_edit_date,  # type: ignore[arg-type]
            type=plannedTour.type,
            gpxFileName=plannedTour.gpxFileName,
            distance=None,
            sharedUsers=[str(user.id) for user in plannedTour.shared_users],
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
        plannedTour.user_id = current_user.id
        plannedTour.last_edit_date = datetime.now()  # type: ignore[assignment]

        newGpxFileName = handleGpxTrack(request.files, uploadFolder)
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

    return plannedTours


def __get_user_models(users: list[User]) -> list[SharedUserModel]:
    sharedUserModels = []
    for user in users:
        sharedUserModels.append(SharedUserModel(user.id, user.username))
    return sharedUserModels
