import logging
import uuid
from typing import Any

from flask import Blueprint, render_template, abort, redirect, url_for, request
from flask_login import login_required, current_user
from flask_pydantic import validate
from pydantic import ConfigDict, field_validator

from sporttracker.blueprints.Sports import BaseSportFormModel
from sporttracker.logic import Constants
from sporttracker.logic.GpxService import GpxService
from sporttracker.logic.model.CustomSportField import CustomSportField
from sporttracker.logic.model.DistanceSport import (
    DistanceSport,
    get_distance_sport_by_id,
)
from sporttracker.logic.model.Participant import get_participants_by_ids, get_participants
from sporttracker.logic.model.PlannedTour import get_planned_tours, get_planned_tour_by_id
from sporttracker.logic.model.Sport import get_sport_names_by_type
from sporttracker.logic.model.WorkoutType import WorkoutType
from sporttracker.logic.model.db import db

LOGGER = logging.getLogger(Constants.APP_NAME)


class DistanceSportFormModel(BaseSportFormModel):
    distance: float
    plannedTourId: str = '-1'
    averageHeartRate: int | None = None
    elevationSum: int | None = None
    gpxFileName: str | None = None
    hasFitFile: bool = False
    shareCode: str | None = None

    model_config = ConfigDict(
        extra='allow',
    )

    @field_validator(*['averageHeartRate', 'elevationSum'], mode='before')
    def averageHeartRateCheck(cls, value: str, info) -> str | None:
        if isinstance(value, str):
            value = value.strip()
        if value == '':
            return None
        return value


def construct_blueprint(gpxService: GpxService, tileHuntingSettings: dict[str, Any]):
    distanceSports = Blueprint(
        'distanceSports', __name__, static_folder='static', url_prefix='/distanceSports'
    )

    @distanceSports.route('/post', methods=['POST'])
    @login_required
    @validate()
    def addPost(form: DistanceSportFormModel):
        gpxMetadataId = gpxService.handle_gpx_upload_for_sport(request.files)

        participantIds = [int(item) for item in request.form.getlist('participants')]
        participants = get_participants_by_ids(participantIds)
        if form.plannedTourId == '-1':
            plannedTour = None
        else:
            plannedTour = get_planned_tour_by_id(int(form.plannedTourId))

        sport = DistanceSport(
            name=form.name,
            type=WorkoutType(form.type),  # type: ignore[call-arg]
            start_time=form.calculate_start_time(),
            duration=form.calculate_duration(),
            distance=form.distance * 1000,
            average_heart_rate=form.averageHeartRate,
            elevation_sum=form.elevationSum,
            gpx_metadata_id=gpxMetadataId,
            custom_fields=form.model_extra,
            user_id=current_user.id,
            participants=participants,
            share_code=form.shareCode if form.shareCode else None,
            planned_tour=plannedTour,
        )

        LOGGER.debug(f'Saved new distance sport: {sport}')
        db.session.add(sport)
        db.session.commit()

        if gpxMetadataId is not None:
            gpxService.add_visited_tiles_for_sport(
                sport, tileHuntingSettings['baseZoomLevel'], current_user.id
            )

        return redirect(
            url_for(
                'sports.listSports',
                year=sport.start_time.year,  # type: ignore[attr-defined]
                month=sport.start_time.month,  # type: ignore[attr-defined]
            )
        )

    @distanceSports.route('/edit/<int:sport_id>')
    @login_required
    def edit(sport_id: int):
        sport = get_distance_sport_by_id(sport_id)

        if sport is None:
            abort(404)

        gpxFileName = None
        gpxMetadata = sport.get_gpx_metadata()
        if gpxMetadata is not None:
            gpxFileName = gpxMetadata.gpx_file_name

        sportModel = DistanceSportFormModel(
            name=sport.name,  # type: ignore[arg-type]
            type=sport.type,
            date=sport.start_time.strftime('%Y-%m-%d'),  # type: ignore[attr-defined]
            time=sport.start_time.strftime('%H:%M'),  # type: ignore[attr-defined]
            distance=sport.distance / 1000,
            durationHours=sport.duration // 3600,
            durationMinutes=sport.duration % 3600 // 60,
            durationSeconds=sport.duration % 3600 % 60,
            averageHeartRate=sport.average_heart_rate,
            elevationSum=sport.elevation_sum,
            gpxFileName=gpxFileName,
            hasFitFile=gpxService.has_fit_file(gpxFileName),
            participants=[str(item.id) for item in sport.participants],
            shareCode=sport.share_code,
            plannedTourId=str(sport.planned_tour.id) if sport.planned_tour else '-1',
            **sport.custom_fields,
        )

        customFields = (
            CustomSportField.query.filter(CustomSportField.user_id == current_user.id)
            .filter(CustomSportField.sport_type == sport.type)
            .all()
        )

        return render_template(
            f'sports/sport{sport.type.name.capitalize()}Form.jinja2',
            sport=sportModel,
            sport_id=sport_id,
            customFields=customFields,
            participants=get_participants(),
            sportNames=get_sport_names_by_type(sport.type),
            plannedTours=get_planned_tours([sport.type]),
        )

    @distanceSports.route('/edit/<int:sport_id>', methods=['POST'])
    @login_required
    @validate()
    def editPost(sport_id: int, form: DistanceSportFormModel):
        sport = get_distance_sport_by_id(sport_id)

        if sport is None:
            abort(404)

        if form.plannedTourId == '-1':
            plannedTour = None
        else:
            plannedTour = get_planned_tour_by_id(int(form.plannedTourId))

        sport.name = form.name  # type: ignore[assignment]
        sport.start_time = form.calculate_start_time()  # type: ignore[assignment]
        sport.distance = form.distance * 1000  # type: ignore[assignment]
        sport.duration = form.calculate_duration()  # type: ignore[assignment]
        sport.average_heart_rate = form.averageHeartRate  # type: ignore[assignment]
        sport.elevation_sum = form.elevationSum  # type: ignore[assignment]
        participantIds = [int(item) for item in request.form.getlist('participants')]
        sport.participants = get_participants_by_ids(participantIds)
        sport.share_code = form.shareCode if form.shareCode else None  # type: ignore[assignment]
        sport.planned_tour = plannedTour  # type: ignore[assignment]

        shouldUpdateVisitedTiles = False
        newGpxMetadataId = gpxService.handle_gpx_upload_for_sport(request.files)
        if sport.gpx_metadata_id is None:
            sport.gpx_metadata_id = newGpxMetadataId
            shouldUpdateVisitedTiles = True
        else:
            if newGpxMetadataId is not None:
                gpxService.delete_gpx(sport, current_user.id)
                sport.gpx_metadata_id = newGpxMetadataId
                shouldUpdateVisitedTiles = True

        sport.custom_fields = form.model_extra

        db.session.commit()

        if shouldUpdateVisitedTiles and sport.gpx_metadata_id is not None:
            gpxService.add_visited_tiles_for_sport(
                sport, tileHuntingSettings['baseZoomLevel'], current_user.id
            )

        LOGGER.debug(f'Updated distance sport: {sport}')

        return redirect(
            url_for(
                'sports.listSports',
                year=sport.start_time.year,  # type: ignore[attr-defined]
                month=sport.start_time.month,  # type: ignore[attr-defined]
            )
        )

    @distanceSports.route('/delete/<int:sport_id>')
    @login_required
    def delete(sport_id: int):
        sport = get_distance_sport_by_id(sport_id)

        if sport is None:
            abort(404)

        gpxService.delete_gpx(sport, current_user.id)

        LOGGER.debug(f'Deleted distance sport: {sport}')
        db.session.delete(sport)
        db.session.commit()

        return redirect(url_for('sports.listSports'))

    @distanceSports.route('/createShareCode')
    @login_required
    def createShareCode():
        shareCode = uuid.uuid4().hex
        return {
            'url': url_for('maps.showSharedSingleTrack', shareCode=shareCode, _external=True),
            'shareCode': shareCode,
        }

    return distanceSports
