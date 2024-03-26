import logging
import os
from dataclasses import dataclass
from datetime import datetime, date

import flask_babel
from babel.dates import get_month_names
from dateutil.relativedelta import relativedelta
from flask import Blueprint, render_template, abort, redirect, url_for, request
from flask_babel import format_datetime
from flask_login import login_required, current_user
from flask_pydantic import validate
from pydantic import BaseModel, ConfigDict, field_validator

from sporttracker.blueprints.GpxTracks import handleGpxTrack
from sporttracker.logic import Constants
from sporttracker.logic.QuickFilterState import get_quick_filter_state_from_session
from sporttracker.logic.model.CustomTrackField import CustomTrackField
from sporttracker.logic.model.MonthGoal import (
    MonthGoalSummary,
    get_goal_summaries_by_year_and_month_and_types,
)
from sporttracker.logic.model.Participant import get_participants_by_ids, get_participants
from sporttracker.logic.model.Track import (
    Track,
    get_tracks_by_year_and_month_by_type,
    TrackType,
    get_track_names_by_track_type,
    get_available_years,
)
from sporttracker.logic.model.User import User
from sporttracker.logic.model.db import db

LOGGER = logging.getLogger(Constants.APP_NAME)


@dataclass
class MonthModel:
    name: str
    tracks: list[Track]
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
    averageHeartRate: int | None = None
    elevationSum: int | None = None
    gpxFileName: str | None = None
    participants: list[str] | str | None = None

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


def construct_blueprint(uploadFolder: str):
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

        monthRightSide = MonthModel(
            format_datetime(monthRightSideDate, format='MMMM yyyy'),
            get_tracks_by_year_and_month_by_type(
                monthRightSideDate.year,
                monthRightSideDate.month,
                quickFilterState.get_active_types(),
            ),
            get_goal_summaries_by_year_and_month_and_types(
                monthRightSideDate.year,
                monthRightSideDate.month,
                quickFilterState.get_active_types(),
            ),
        )

        monthLeftSideDate = monthRightSideDate - relativedelta(months=1)
        monthLeftSide = MonthModel(
            format_datetime(monthLeftSideDate, format='MMMM yyyy'),
            get_tracks_by_year_and_month_by_type(
                monthLeftSideDate.year, monthLeftSideDate.month, quickFilterState.get_active_types()
            ),
            get_goal_summaries_by_year_and_month_and_types(
                monthLeftSideDate.year, monthLeftSideDate.month, quickFilterState.get_active_types()
            ),
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
            availableYears=get_available_years(),
            monthNames=list(
                get_month_names(width='wide', locale=flask_babel.get_locale()).values()
            ),
        )

    @tracks.route('/add')
    @login_required
    def add():
        return render_template('tracks/trackChooser.jinja2')

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
        )

    @tracks.route('/post', methods=['POST'])
    @login_required
    @validate()
    def addPost(form: TrackFormModel):
        gpxFileName = handleGpxTrack(request.files, uploadFolder)

        participantIds = [int(item) for item in request.form.getlist('participants')]
        participants = get_participants_by_ids(participantIds)

        track = Track(
            name=form.name,
            type=TrackType(form.type),  # type: ignore[call-arg]
            startTime=form.calculate_start_time(),
            duration=form.calculate_duration(),
            distance=form.distance * 1000,
            averageHeartRate=form.averageHeartRate,
            elevationSum=form.elevationSum,
            gpxFileName=gpxFileName,
            custom_fields=form.model_extra,
            user_id=current_user.id,
            participants=participants,
        )
        LOGGER.debug(f'Saved new track: {track}')
        db.session.add(track)
        db.session.commit()

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
        track: Track | None = (
            Track.query.join(User)
            .filter(User.username == current_user.username)
            .filter(Track.id == track_id)
            .first()
        )

        if track is None:
            abort(404)

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
            gpxFileName=track.gpxFileName,
            participants=[str(item.id) for item in track.participants],
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
        )

    @tracks.route('/edit/<int:track_id>', methods=['POST'])
    @login_required
    @validate()
    def editPost(track_id: int, form: TrackFormModel):
        track = (
            Track.query.join(User)
            .filter(User.username == current_user.username)
            .filter(Track.id == track_id)
            .first()
        )

        if track is None:
            abort(404)

        track.name = form.name
        track.startTime = form.calculate_start_time()
        track.distance = form.distance * 1000
        track.duration = form.calculate_duration()
        track.averageHeartRate = form.averageHeartRate
        track.elevationSum = form.elevationSum
        participantIds = [int(item) for item in request.form.getlist('participants')]
        track.participants = get_participants_by_ids(participantIds)

        newGpxFileName = handleGpxTrack(request.files, uploadFolder)
        if track.gpxFileName is None:
            track.gpxFileName = newGpxFileName
        else:
            if newGpxFileName is not None:
                track.gpxFileName = newGpxFileName

        track.custom_fields = form.model_extra

        LOGGER.debug(f'Updated track: {track}')
        db.session.commit()

        return redirect(
            url_for('tracks.listTracks', year=track.startTime.year, month=track.startTime.month)
        )

    @tracks.route('/delete/<int:track_id>')
    @login_required
    def delete(track_id: int):
        track = (
            Track.query.join(User)
            .filter(User.username == current_user.username)
            .filter(Track.id == track_id)
            .first()
        )

        if track is None:
            abort(404)

        if track.gpxFileName is not None:
            try:
                os.remove(os.path.join(uploadFolder, track.gpxFileName))
                LOGGER.debug(
                    f'Deleted linked gpx file "{track.gpxFileName}" for track with id {track_id}'
                )
            except OSError as e:
                LOGGER.error(e)

        LOGGER.debug(f'Deleted track: {track}')
        db.session.delete(track)
        db.session.commit()

        return redirect(url_for('tracks.listTracks'))

    return tracks
