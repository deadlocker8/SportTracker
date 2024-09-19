import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from flask import Blueprint, render_template, redirect, url_for, abort, request, Response
from flask_login import login_required, current_user
from flask_pydantic import validate
from pydantic import BaseModel

from sporttracker.logic import Constants
from sporttracker.logic.GpxService import GpxService
from sporttracker.logic.QuickFilterState import get_quick_filter_state_from_session
from sporttracker.logic.model.GpxMetadata import GpxMetadata
from sporttracker.logic.model.PlannedTour import (
    PlannedTour,
    get_planned_tour_by_id,
    TravelType,
    TravelDirection,
    get_planned_tours,
)
from sporttracker.logic.model.Track import get_track_ids_by_planned_tour, Track
from sporttracker.logic.model.TrackType import TrackType
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
class LinkedTrack:
    id: int
    startTime: datetime


@dataclass
class PlannedTourModel:
    id: int
    name: str
    creationDate: datetime
    lastEditDate: datetime
    type: TrackType
    gpxMetadata: GpxMetadata | None
    sharedUsers: list[str]
    ownerId: str
    ownerName: str
    arrivalMethod: TravelType
    departureMethod: TravelType
    direction: TravelDirection
    shareCode: str | None
    linkedTracks: list[LinkedTrack]

    @staticmethod
    def __get_linked_tracks_by_planned_tour(plannedTour: PlannedTour) -> list[LinkedTrack]:
        linkedTrack = (
            Track.query.filter(Track.user_id == current_user.id)
            .filter(Track.plannedTour == plannedTour)
            .order_by(Track.startTime.asc())
            .all()
        )

        if linkedTrack is None:
            return []

        result = []
        for track in linkedTrack:
            result.append(LinkedTrack(int(track.id), track.startTime))

        return result

    @staticmethod
    def create_from_tour(
        plannedTour: PlannedTour,
        includeLinkedTracks: bool,
    ) -> 'PlannedTourModel':
        gpxMetadata = plannedTour.get_gpx_metadata()

        linkedTracks = []
        if includeLinkedTracks:
            linkedTracks = PlannedTourModel.__get_linked_tracks_by_planned_tour(plannedTour)

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
            shareCode=plannedTour.share_code,
            linkedTracks=linkedTracks,
        )


class PlannedTourFormModel(BaseModel):
    name: str
    type: str
    arrivalMethod: str
    departureMethod: str
    direction: str
    sharedUsers: list[str] | str | None = None
    shareCode: str | None = None


class PlannedTourEditFormModel(BaseModel):
    name: str
    type: str
    arrivalMethod: TravelType
    departureMethod: TravelType
    direction: TravelDirection
    ownerId: str
    ownerName: str
    sharedUsers: list[str] | str | None = None
    shareCode: str | None = None
    gpxFileName: str | None = None


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

        tours = get_planned_tours(quickFilterState.get_active_types())

        plannedTourList: list[PlannedTourModel] = []
        for tour in tours:
            plannedTourList.append(PlannedTourModel.create_from_tour(tour, True))

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
        gpxMetadataId = gpxService.handle_gpx_upload_for_planned_tour(
            request.files, gpxPreviewImageSettings
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
            gpx_metadata_id=gpxMetadataId,
            shared_users=sharedUsers,
            arrival_method=TravelType(form.arrivalMethod),  # type: ignore[call-arg]
            departure_method=TravelType(form.departureMethod),  # type: ignore[call-arg]
            direction=TravelDirection(form.direction),  # type: ignore[call-arg]
            share_code=form.shareCode,
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
            shareCode=plannedTour.share_code,
            gpxFileName=gpxFileName,
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
        plannedTour.share_code = form.shareCode if form.shareCode else None  # type: ignore[assignment]

        newGpxMetadataId = gpxService.handle_gpx_upload_for_planned_tour(
            request.files, gpxPreviewImageSettings
        )
        if plannedTour.gpx_metadata_id is None:
            plannedTour.gpx_metadata_id = newGpxMetadataId
        else:
            if newGpxMetadataId is not None:
                gpxService.delete_gpx(plannedTour)
                plannedTour.gpx_metadata_id = newGpxMetadataId

        sharedUserIds = [int(item) for item in request.form.getlist('sharedUsers')]
        sharedUsers = get_users_by_ids(sharedUserIds)
        plannedTour.shared_users = sharedUsers

        # The list of shared users may have changed.
        # All tracks that link to this planned tour must be checked, whether they are owned by the owner of the
        # planned tour or if the planned tour is still shared to the owner of the track.
        linkedTrackIds = get_track_ids_by_planned_tour(plannedTour)
        for trackId in linkedTrackIds:
            track = Track.query.filter().filter(Track.id == trackId).first()
            if track.user_id == plannedTour.user_id:
                continue

            if track.user_id in sharedUserIds:
                continue

            track.plannedTour = None
            LOGGER.debug(f'Removed linked planned tour from track: {trackId}')
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

        gpxService.delete_gpx(plannedTour)

        linkedTrackIds = get_track_ids_by_planned_tour(plannedTour)
        for trackId in linkedTrackIds:
            track = Track.query.filter().filter(Track.id == trackId).first()
            track.plannedTour = None
            LOGGER.debug(f'Removed linked planned tour from track: {trackId}')
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

    return plannedTours


def __get_user_models(users: list[User]) -> list[SharedUserModel]:
    sharedUserModels = []
    for user in users:
        sharedUserModels.append(SharedUserModel(user.id, user.username))
    return sharedUserModels
