import logging
import os
from datetime import datetime

from flask import Blueprint, render_template, abort, url_for, session, redirect, request
from flask_login import login_required, current_user
from sqlalchemy import func, extract, or_

from sporttracker.blueprints.PlannedTours import PlannedTourModel
from sporttracker.logic import Constants
from sporttracker.logic.GpxService import GpxService
from sporttracker.logic.QuickFilterState import get_quick_filter_state_from_session
from sporttracker.logic.model.PlannedTour import get_planned_tour_by_id, PlannedTour
from sporttracker.logic.model.Track import Track, get_available_years, get_track_by_id
from sporttracker.logic.model.User import get_user_by_id

LOGGER = logging.getLogger(Constants.APP_NAME)


def createGpxInfo(trackId: int, trackName: str, trackStartTime: datetime) -> dict[str, str | int]:
    return {
        'trackId': trackId,
        'gpxUrl': url_for('gpxTracks.downloadGpxTrackByTrackId', track_id=trackId),
        'trackUrl': url_for('tracks.edit', track_id=trackId),
        'trackName': f'{trackStartTime.strftime("%Y-%m-%d")} - {trackName}',
    }


def createGpxInfoPlannedTour(tourId: int, tourName: str) -> dict[str, str | int]:
    return {
        'trackId': tourId,
        'gpxUrl': url_for('gpxTracks.downloadGpxTrackByPlannedTourId', tour_id=tourId),
        'trackUrl': url_for('plannedTours.edit', tour_id=tourId),
        'trackName': tourName,
    }


def construct_blueprint(uploadFolder: str):
    maps = Blueprint('maps', __name__, static_folder='static')

    @maps.route('/map')
    @login_required
    def showAllTracksOnMap():
        quickFilterState = get_quick_filter_state_from_session()
        availableYears = get_available_years()
        yearFilterState = __get_map_year_filter_state_from_session(availableYears)

        gpxInfo = []

        funcStartTime = func.max(Track.startTime)
        tracks = (
            Track.query.with_entities(func.max(Track.id), Track.name, funcStartTime)
            .filter(Track.user_id == current_user.id)
            .filter(Track.gpxFileName.isnot(None))
            .filter(Track.type.in_(quickFilterState.get_active_types()))
            .filter(extract('year', Track.startTime).in_(yearFilterState))
            .group_by(Track.name)
            .order_by(funcStartTime.desc())
            .all()
        )

        for track in tracks:
            trackId, trackName, trackStartTime = track
            gpxInfo.append(createGpxInfo(trackId, trackName, trackStartTime))

        return render_template(
            'maps/mapMultipleTracks.jinja2',
            gpxInfo=gpxInfo,
            quickFilterState=quickFilterState,
            yearFilterState=yearFilterState,
            availableYears=availableYears,
            mapMode='tracks',
            redirectUrl='maps.showAllTracksOnMap',
        )

    @maps.route('/map/<int:track_id>')
    @login_required
    def showSingleTrack(track_id: int):
        track = get_track_by_id(track_id)

        if track is None:
            abort(404)

        if track.gpxFileName is None:
            gpxMetaInfo = None
        else:
            gpxTrackPath = os.path.join(uploadFolder, str(track.gpxFileName))
            gpxService = GpxService(gpxTrackPath)
            gpxMetaInfo = gpxService.get_meta_info()

        return render_template(
            'maps/mapSingleTrack.jinja2',
            track=track,
            gpxMetaInfo=gpxMetaInfo,
            ownerName=get_user_by_id(track.user_id).username,
            gpxUrl=url_for('gpxTracks.downloadGpxTrackByTrackId', track_id=track_id),
        )

    @maps.route('/map/plannedTour/<int:tour_id>')
    @login_required
    def showPlannedTour(tour_id: int):
        plannedTour = get_planned_tour_by_id(tour_id)

        if plannedTour is None:
            abort(404)

        if plannedTour.gpxFileName is None:
            gpxMetaInfo = None
        else:
            gpxTrackPath = os.path.join(uploadFolder, str(plannedTour.gpxFileName))
            gpxService = GpxService(gpxTrackPath)
            gpxMetaInfo = gpxService.get_meta_info()

        tourModel = PlannedTourModel(
            id=plannedTour.id,
            name=plannedTour.name,  # type: ignore[arg-type]
            creationDate=plannedTour.creation_date,  # type: ignore[arg-type]
            lastEditDate=plannedTour.last_edit_date,  # type: ignore[arg-type]
            type=plannedTour.type,
            gpxFileName=plannedTour.gpxFileName,
            gpxMetaInfo=gpxMetaInfo,
            sharedUsers=[str(user.id) for user in plannedTour.shared_users],
            ownerId=str(plannedTour.user_id),
            ownerName=get_user_by_id(plannedTour.user_id).username,
            arrivalMethod=plannedTour.arrival_method,
            departureMethod=plannedTour.departure_method,
            direction=plannedTour.direction,
        )

        return render_template(
            'maps/mapPlannedTour.jinja2',
            plannedTour=tourModel,
            gpxUrl=url_for('gpxTracks.downloadGpxTrackByPlannedTourId', tour_id=tour_id),
        )

    @maps.route('/toggleYears', methods=['POST'])
    @login_required
    def toggleYears():
        activeYears = [int(item) for item in request.form.getlist('activeYears')]

        session['mapYearFilterState'] = activeYears

        return redirect(url_for('maps.showAllTracksOnMap'))

    @maps.route('/map/plannedTours')
    @login_required
    def showAllPlannedToursOnMap():
        quickFilterState = get_quick_filter_state_from_session()

        gpxInfo = []

        plannedTours: list[PlannedTour] = (
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

        for tour in plannedTours:
            gpxInfo.append(createGpxInfoPlannedTour(tour.id, tour.name))  # type: ignore[arg-type]

        return render_template(
            'maps/mapMultipleTracks.jinja2',
            gpxInfo=gpxInfo,
            quickFilterState=quickFilterState,
            mapMode='plannedTours',
            redirectUrl='maps.showAllPlannedToursOnMap',
        )

    return maps


def __get_map_year_filter_state_from_session(availableYears: list[int]) -> list[int]:
    if 'mapYearFilterState' not in session:
        session['mapYearFilterState'] = availableYears

    return sorted(session['mapYearFilterState'])
