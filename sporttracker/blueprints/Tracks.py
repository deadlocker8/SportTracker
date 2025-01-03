import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, date
from typing import Any

import flask_babel
from babel.dates import get_month_names
from dateutil.relativedelta import relativedelta
from flask import Blueprint, render_template, abort, redirect, url_for, request
from flask_babel import format_datetime
from flask_login import login_required, current_user
from flask_pydantic import validate
from pydantic import BaseModel, ConfigDict, field_validator

from sporttracker.logic import Constants
from sporttracker.logic.DateTimeAccess import DateTimeAccess
from sporttracker.logic.GpxService import GpxService
from sporttracker.logic.QuickFilterState import (
    get_quick_filter_state_from_session,
    QuickFilterState,
)
from sporttracker.logic.model.CustomTrackField import CustomTrackField
from sporttracker.logic.model.GpxMetadata import GpxMetadata
from sporttracker.logic.model.MaintenanceEventInstance import (
    MaintenanceEvent,
    get_maintenance_events_by_year_and_month_by_type,
)
from sporttracker.logic.model.MonthGoal import (
    MonthGoalSummary,
    get_goal_summaries_by_year_and_month_and_types,
)
from sporttracker.logic.model.Participant import get_participants_by_ids, get_participants
from sporttracker.logic.model.PlannedTour import get_planned_tours, get_planned_tour_by_id
from sporttracker.logic.model.Track import (
    Track,
    get_tracks_by_year_and_month_by_type,
    get_track_names_by_track_type,
    get_available_years,
    get_track_by_id,
)
from sporttracker.logic.model.TrackType import TrackType
from sporttracker.logic.model.User import get_user_by_id
from sporttracker.logic.model.db import db

LOGGER = logging.getLogger(Constants.APP_NAME)


@dataclass
class TrackModel(DateTimeAccess):
    id: int
    name: str
    type: str
    startTime: datetime
    distance: int
    duration: int
    averageHeartRate: int | None
    elevationSum: int | None
    gpxMetadata: GpxMetadata | None
    participants: list[str]
    shareCode: str | None
    ownerName: str

    @staticmethod
    def create_from_track(
        track: Track,
    ) -> 'TrackModel':
        return TrackModel(
            id=track.id,
            name=track.name,  # type: ignore[arg-type]
            type=track.type,
            startTime=track.startTime,  # type: ignore[arg-type]
            distance=track.distance,
            duration=track.duration,
            averageHeartRate=track.averageHeartRate,
            elevationSum=track.elevationSum,
            gpxMetadata=track.get_gpx_metadata(),
            participants=[str(item.id) for item in track.participants],
            shareCode=track.share_code,
            ownerName=get_user_by_id(track.user_id).username,
        )

    def get_date_time(self) -> datetime:
        return self.startTime


@dataclass
class MonthModel:
    name: str
    entries: list[TrackModel | MaintenanceEvent]
    goals: list[MonthGoalSummary]


class TrackFormModel(BaseModel):
    name: str
    type: str
    date: str
    time: str
    distance: float
    durationHours: int
    durationMinutes: int
    durationSeconds: int
    plannedTourId: str = '-1'
    averageHeartRate: int | None = None
    elevationSum: int | None = None
    gpxFileName: str | None = None
    hasFitFile: bool = False
    participants: list[str] | str | None = None
    shareCode: str | None = None

    model_config = ConfigDict(
        extra='allow',
    )

    def calculate_start_time(self) -> datetime:
        return datetime.strptime(f'{self.date} {self.time}', '%Y-%m-%d %H:%M')

    def calculate_duration(self) -> int:
        return 3600 * self.durationHours + 60 * self.durationMinutes + self.durationSeconds

    @field_validator(*['averageHeartRate', 'elevationSum'], mode='before')
    def averageHeartRateCheck(cls, value: str, info) -> str | None:
        if isinstance(value, str):
            value = value.strip()
        if value == '':
            return None
        return value


def construct_blueprint(gpxService: GpxService, tileHuntingSettings: dict[str, Any]):
    tracks = Blueprint('tracks', __name__, static_folder='static', url_prefix='/tracks')

    @tracks.route('/', defaults={'year': None, 'month': None})
    @tracks.route('/<int:year>/<int:month>')
    @login_required
    def listTracks(year: int, month: int):
        if year is None or month is None:
            now = datetime.now().date()
            return redirect(url_for('tracks.listTracks', year=now.year, month=now.month))
        else:
            monthRightSideDate = date(year=year, month=month, day=1)

        quickFilterState = get_quick_filter_state_from_session()

        monthRightSide = __get_month_model(monthRightSideDate, quickFilterState)

        monthLeftSideDate = monthRightSideDate - relativedelta(months=1)
        monthLeftSide = __get_month_model(
            monthLeftSideDate,
            quickFilterState,
        )

        nextMonthDate = monthRightSideDate + relativedelta(months=1)

        return render_template(
            'tracks/tracks.jinja2',
            monthLeftSide=monthLeftSide,
            monthRightSide=monthRightSide,
            previousMonthDate=monthLeftSideDate,
            nextMonthDate=nextMonthDate,
            currentMonthDate=datetime.now().date(),
            quickFilterState=quickFilterState,
            year=year,
            month=month,
            availableYears=get_available_years(current_user.id) or [datetime.now().year],
            monthNames=list(
                get_month_names(width='wide', locale=flask_babel.get_locale()).values()
            ),
        )

    @tracks.route('/add')
    @login_required
    def add():
        return render_template(
            'tracks/trackChooser.jinja2',
        )

    @tracks.route('/add/<string:track_type>')
    @login_required
    def addType(track_type: str):
        trackType = TrackType(track_type)  # type: ignore[call-arg]

        customFields = (
            CustomTrackField.query.filter(CustomTrackField.user_id == current_user.id)
            .filter(CustomTrackField.track_type == trackType)
            .all()
        )

        return render_template(
            f'tracks/track{track_type.capitalize()}Form.jinja2',
            customFields=customFields,
            participants=get_participants(),
            trackNames=get_track_names_by_track_type(trackType),
            plannedTours=get_planned_tours([trackType]),
        )

    @tracks.route('/post', methods=['POST'])
    @login_required
    @validate()
    def addPost(form: TrackFormModel):
        gpxMetadataId = gpxService.handle_gpx_upload_for_track(request.files)

        participantIds = [int(item) for item in request.form.getlist('participants')]
        participants = get_participants_by_ids(participantIds)
        if form.plannedTourId == '-1':
            plannedTour = None
        else:
            plannedTour = get_planned_tour_by_id(int(form.plannedTourId))

        track = Track(
            name=form.name,
            type=TrackType(form.type),  # type: ignore[call-arg]
            startTime=form.calculate_start_time(),
            duration=form.calculate_duration(),
            distance=form.distance * 1000,
            averageHeartRate=form.averageHeartRate,
            elevationSum=form.elevationSum,
            gpx_metadata_id=gpxMetadataId,
            custom_fields=form.model_extra,
            user_id=current_user.id,
            participants=participants,
            share_code=form.shareCode if form.shareCode else None,
            plannedTour=plannedTour,
        )
        track.clear_attributes_for_track_type()

        LOGGER.debug(f'Saved new track: {track}')
        db.session.add(track)
        db.session.commit()

        if gpxMetadataId is not None:
            gpxService.add_visited_tiles_for_track(
                track, tileHuntingSettings['baseZoomLevel'], current_user.id
            )

        return redirect(
            url_for(
                'tracks.listTracks',
                year=track.startTime.year,  # type: ignore[attr-defined]
                month=track.startTime.month,  # type: ignore[attr-defined]
            )
        )

    @tracks.route('/edit/<int:track_id>')
    @login_required
    def edit(track_id: int):
        track = get_track_by_id(track_id)

        if track is None:
            abort(404)

        gpxFileName = None
        gpxMetadata = track.get_gpx_metadata()
        if gpxMetadata is not None:
            gpxFileName = gpxMetadata.gpx_file_name

        trackModel = TrackFormModel(
            name=track.name,  # type: ignore[arg-type]
            type=track.type,
            date=track.startTime.strftime('%Y-%m-%d'),  # type: ignore[attr-defined]
            time=track.startTime.strftime('%H:%M'),  # type: ignore[attr-defined]
            distance=track.distance / 1000,
            durationHours=track.duration // 3600,
            durationMinutes=track.duration % 3600 // 60,
            durationSeconds=track.duration % 3600 % 60,
            averageHeartRate=track.averageHeartRate,
            elevationSum=track.elevationSum,
            gpxFileName=gpxFileName,
            hasFitFile=gpxService.has_fit_file(gpxFileName),
            participants=[str(item.id) for item in track.participants],
            shareCode=track.share_code,
            plannedTourId=str(track.plannedTour.id) if track.plannedTour else '-1',
            **track.custom_fields,
        )

        customFields = (
            CustomTrackField.query.filter(CustomTrackField.user_id == current_user.id)
            .filter(CustomTrackField.track_type == track.type)
            .all()
        )

        return render_template(
            f'tracks/track{track.type.name.capitalize()}Form.jinja2',
            track=trackModel,
            track_id=track_id,
            customFields=customFields,
            participants=get_participants(),
            trackNames=get_track_names_by_track_type(track.type),
            plannedTours=get_planned_tours([track.type]),
        )

    @tracks.route('/edit/<int:track_id>', methods=['POST'])
    @login_required
    @validate()
    def editPost(track_id: int, form: TrackFormModel):
        track = get_track_by_id(track_id)

        if track is None:
            abort(404)

        if form.plannedTourId == '-1':
            plannedTour = None
        else:
            plannedTour = get_planned_tour_by_id(int(form.plannedTourId))

        track.name = form.name  # type: ignore[assignment]
        track.startTime = form.calculate_start_time()  # type: ignore[assignment]
        track.distance = form.distance * 1000  # type: ignore[assignment]
        track.duration = form.calculate_duration()  # type: ignore[assignment]
        track.averageHeartRate = form.averageHeartRate  # type: ignore[assignment]
        track.elevationSum = form.elevationSum  # type: ignore[assignment]
        participantIds = [int(item) for item in request.form.getlist('participants')]
        track.participants = get_participants_by_ids(participantIds)
        track.share_code = form.shareCode if form.shareCode else None  # type: ignore[assignment]
        track.plannedTour = plannedTour  # type: ignore[assignment]

        track.clear_attributes_for_track_type()

        shouldUpdateVisitedTiles = False
        newGpxMetadataId = gpxService.handle_gpx_upload_for_track(request.files)
        if track.gpx_metadata_id is None:
            track.gpx_metadata_id = newGpxMetadataId
            shouldUpdateVisitedTiles = True
        else:
            if newGpxMetadataId is not None:
                gpxService.delete_gpx(track, current_user.id)
                track.gpx_metadata_id = newGpxMetadataId
                shouldUpdateVisitedTiles = True

        track.custom_fields = form.model_extra

        db.session.commit()

        if shouldUpdateVisitedTiles and track.gpx_metadata_id is not None:
            gpxService.add_visited_tiles_for_track(
                track, tileHuntingSettings['baseZoomLevel'], current_user.id
            )

        LOGGER.debug(f'Updated track: {track}')

        return redirect(
            url_for(
                'tracks.listTracks',
                year=track.startTime.year,  # type: ignore[attr-defined]
                month=track.startTime.month,  # type: ignore[attr-defined]
            )
        )

    @tracks.route('/delete/<int:track_id>')
    @login_required
    def delete(track_id: int):
        track = get_track_by_id(track_id)

        if track is None:
            abort(404)

        gpxService.delete_gpx(track, current_user.id)

        LOGGER.debug(f'Deleted track: {track}')
        db.session.delete(track)
        db.session.commit()

        return redirect(url_for('tracks.listTracks'))

    @tracks.route('/createShareCode')
    @login_required
    def createShareCode():
        shareCode = uuid.uuid4().hex
        return {
            'url': url_for('maps.showSharedSingleTrack', shareCode=shareCode, _external=True),
            'shareCode': shareCode,
        }

    return tracks


def __get_month_model(
    monthDate: date,
    quickFilterState: QuickFilterState,
) -> MonthModel:
    tracks = get_tracks_by_year_and_month_by_type(
        monthDate.year,
        monthDate.month,
        quickFilterState.get_active_types(),
    )

    trackModels = []
    for track in tracks:
        trackModels.append(TrackModel.create_from_track(track))

    maintenanceEvents = get_maintenance_events_by_year_and_month_by_type(
        monthDate.year, monthDate.month, quickFilterState.get_active_types()
    )

    entries = trackModels + maintenanceEvents
    entries.sort(key=lambda entry: entry.get_date_time(), reverse=True)

    return MonthModel(
        format_datetime(monthDate, format='MMMM yyyy'),
        entries,
        get_goal_summaries_by_year_and_month_and_types(
            monthDate.year,
            monthDate.month,
            quickFilterState.get_active_types(),
        ),
    )
