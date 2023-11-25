import logging
from dataclasses import dataclass
from datetime import datetime, date

from dateutil.relativedelta import relativedelta
from flask import Blueprint, render_template, abort, redirect, url_for
from flask_login import login_required, current_user
from flask_pydantic import validate
from pydantic import BaseModel, ConfigDict, field_validator

from logic import Constants
from logic.model.Models import Track, get_goal_summaries_by_year_and_month, MonthGoalSummary, TrackType, \
    get_tracks_by_year_and_month_by_type, User, db, CustomTrackField

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


def construct_blueprint():
    tracks = Blueprint('tracks', __name__, static_folder='static', url_prefix='/tracks')

    @tracks.route('/', defaults={'year': None, 'month': None})
    @tracks.route('/<int:year>/<int:month>')
    @login_required
    def listTracks(year: int, month: int):
        if year is None or month is None:
            monthRightSideDate = datetime.now().date()
        else:
            monthRightSideDate = date(year=year, month=month, day=1)

        monthRightSide = MonthModel(monthRightSideDate.strftime('%B %Y'),
                                    get_tracks_by_year_and_month_by_type(monthRightSideDate.year,
                                                                         monthRightSideDate.month,
                                                                         [t for t in TrackType]),
                                    get_goal_summaries_by_year_and_month(monthRightSideDate.year,
                                                                         monthRightSideDate.month))

        monthLeftSideDate = monthRightSideDate - relativedelta(months=1)
        monthLeftSide = MonthModel(monthLeftSideDate.strftime('%B %Y'),
                                   get_tracks_by_year_and_month_by_type(monthLeftSideDate.year,
                                                                        monthLeftSideDate.month,
                                                                        [t.value for t in TrackType]),
                                   get_goal_summaries_by_year_and_month(monthLeftSideDate.year,
                                                                        monthLeftSideDate.month))

        nextMonthDate = monthRightSideDate + relativedelta(months=1)

        return render_template('tracks/tracks.jinja2',
                               monthLeftSide=monthLeftSide,
                               monthRightSide=monthRightSide,
                               previousMonthDate=monthLeftSideDate,
                               nextMonthDate=nextMonthDate,
                               currentMonthDate=datetime.now().date())

    @tracks.route('/add')
    @login_required
    def add():
        return render_template('tracks/trackChooser.jinja2')

    @tracks.route('/add/<string:track_type>')
    @login_required
    def addType(track_type: str):
        customFields = (CustomTrackField.query
                        .filter(CustomTrackField.user_id == current_user.id)
                        .filter(CustomTrackField.track_type == track_type)
                        .all())
        return render_template(f'track{track_type.capitalize()}Form.jinja2',
                               customFields=customFields)

    @tracks.route('/post', methods=['POST'])
    @login_required
    @validate()
    def addPost(form: TrackFormModel):
        track = Track(name=form.name,
                      type=TrackType(form.type),
                      startTime=form.calculate_start_time(),
                      duration=form.calculate_duration(),
                      distance=form.distance * 1000,
                      averageHeartRate=form.averageHeartRate,
                      elevationSum=form.elevationSum,
                      custom_fields=form.model_extra,
                      user_id=current_user.id)
        LOGGER.debug(f'Saved new track: {track}')
        db.session.add(track)
        db.session.commit()

        return redirect(url_for('tracks.listTracks'))

    @tracks.route('/edit/<int:track_id>')
    @login_required
    def edit(track_id: int):
        track: Track | None = (Track.query.join(User)
                               .filter(User.username == current_user.username)
                               .filter(Track.id == track_id)
                               .first())

        if track is None:
            abort(404)

        trackModel = TrackFormModel(
            name=track.name,
            type=track.type,
            date=track.startTime.strftime('%Y-%m-%d'),
            time=track.startTime.strftime('%H:%M'),
            distance=track.distance / 1000,
            durationHours=track.duration // 3600,
            durationMinutes=track.duration % 3600 // 60,
            durationSeconds=track.duration % 3600 % 60,
            averageHeartRate=track.averageHeartRate,
            elevationSum=track.elevationSum,
            **track.custom_fields)

        customFields = (CustomTrackField.query
                        .filter(CustomTrackField.user_id == current_user.id)
                        .filter(CustomTrackField.track_type == track.type)
                        .all())

        return render_template(f'track{track.type.name.capitalize()}Form.jinja2',
                               track=trackModel,
                               track_id=track_id,
                               customFields=customFields)

    @tracks.route('/edit/<int:track_id>', methods=['POST'])
    @login_required
    @validate()
    def editPost(track_id: int, form: TrackFormModel):
        track = (Track.query.join(User)
                 .filter(User.username == current_user.username)
                 .filter(Track.id == track_id)
                 .first())

        if track is None:
            abort(404)

        track.name = form.name
        track.startTime = form.calculate_start_time()
        track.distance = form.distance * 1000
        track.duration = form.calculate_duration()
        track.averageHeartRate = form.averageHeartRate
        track.elevationSum = form.elevationSum
        track.user_id = current_user.id
        track.custom_fields = form.model_extra

        LOGGER.debug(f'Updated track: {track}')
        db.session.commit()

        return redirect(url_for('tracks.listTracks'))

    @tracks.route('/delete/<int:track_id>')
    @login_required
    def delete(track_id: int):
        track = (Track.query.join(User)
                 .filter(User.username == current_user.username)
                 .filter(Track.id == track_id)
                 .first())

        if track is None:
            abort(404)

        LOGGER.debug(f'Deleted biking track: {track}')
        db.session.delete(track)
        db.session.commit()

        return redirect(url_for('tracks.listTracks'))

    return tracks
