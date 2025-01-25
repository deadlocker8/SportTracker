import logging
from typing import Any

from flask import Blueprint, render_template, abort, redirect, url_for, request
from flask_login import login_required, current_user
from flask_pydantic import validate
from pydantic import ConfigDict

from sporttracker.blueprints.Sports import BaseSportFormModel
from sporttracker.logic import Constants
from sporttracker.logic.GpxService import GpxService
from sporttracker.logic.model.CustomSportField import CustomSportField
from sporttracker.logic.model.Participant import get_participants_by_ids, get_participants
from sporttracker.logic.model.PlannedTour import get_planned_tours
from sporttracker.logic.model.Sport import get_sport_names_by_type
from sporttracker.logic.model.SportType import SportType
from sporttracker.logic.model.WorkoutCategory import (
    update_workout_categories_by_sport_id,
    WorkoutCategoryType,
)
from sporttracker.logic.model.WorkoutSport import WorkoutSport, get_workout_sport_by_id
from sporttracker.logic.model.WorkoutType import WorkoutType
from sporttracker.logic.model.db import db

LOGGER = logging.getLogger(Constants.APP_NAME)


class WorkoutSportFormModel(BaseSportFormModel):
    workoutCategories: list[str]
    workoutType: str

    model_config = ConfigDict(
        extra='allow',
    )


def construct_blueprint(gpxService: GpxService, tileHuntingSettings: dict[str, Any]):
    workoutSports = Blueprint(
        'workoutSports', __name__, static_folder='static', url_prefix='/workoutSports'
    )

    @workoutSports.route('/post', methods=['POST'])
    @login_required
    @validate()
    def addPost(form: WorkoutSportFormModel):
        participantIds = [int(item) for item in request.form.getlist('participants')]
        participants = get_participants_by_ids(participantIds)

        sport = WorkoutSport(
            name=form.name,
            type=SportType(form.type),  # type: ignore[call-arg]
            start_time=form.calculate_start_time(),
            duration=form.calculate_duration(),
            custom_fields=form.model_extra,
            user_id=current_user.id,
            participants=participants,
            workout_type=WorkoutType(form.workoutType),  # type: ignore[call-arg]
        )

        workoutCategories = [
            WorkoutCategoryType(value)  # type: ignore[call-arg]
            for key, value in request.form.items()
            if key.startswith('workoutCategories')
        ]
        update_workout_categories_by_sport_id(sport.id, workoutCategories)

        LOGGER.debug(f'Saved new workout sport: {sport}')
        db.session.add(sport)
        db.session.commit()

        return redirect(
            url_for(
                'sports.listSports',
                year=sport.start_time.year,  # type: ignore[attr-defined]
                month=sport.start_time.month,  # type: ignore[attr-defined]
            )
        )

    @workoutSports.route('/edit/<int:sport_id>')
    @login_required
    def edit(sport_id: int):
        sport = get_workout_sport_by_id(sport_id)

        if sport is None:
            abort(404)

        sportModel = WorkoutSportFormModel(
            name=sport.name,  # type: ignore[arg-type]
            type=sport.type,
            date=sport.start_time.strftime('%Y-%m-%d'),  # type: ignore[attr-defined]
            time=sport.start_time.strftime('%H:%M'),  # type: ignore[attr-defined]
            durationHours=sport.duration // 3600,
            durationMinutes=sport.duration % 3600 // 60,
            durationSeconds=sport.duration % 3600 % 60,
            participants=[str(item.id) for item in sport.participants],
            workoutCategories=sport.get_workout_categories(),
            workoutType=sport.workout_type,
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

    @workoutSports.route('/edit/<int:sport_id>', methods=['POST'])
    @login_required
    @validate()
    def editPost(sport_id: int, form: WorkoutSportFormModel):
        sport = get_workout_sport_by_id(sport_id)

        if sport is None:
            abort(404)

        sport.name = form.name  # type: ignore[assignment]
        sport.start_time = form.calculate_start_time()  # type: ignore[assignment]
        sport.duration = form.calculate_duration()  # type: ignore[assignment]
        participantIds = [int(item) for item in request.form.getlist('participants')]
        sport.participants = get_participants_by_ids(participantIds)
        sport.workout_type = None if form.workoutType is None else WorkoutType(form.workoutType)  # type: ignore[call-arg]

        sport.custom_fields = form.model_extra

        workoutCategories = [
            WorkoutCategoryType(value)  # type: ignore[call-arg]
            for key, value in request.form.items()
            if key.startswith('workoutCategories')
        ]
        update_workout_categories_by_sport_id(sport.id, workoutCategories)

        db.session.commit()

        LOGGER.debug(f'Updated workout sport: {sport}')

        return redirect(
            url_for(
                'sports.listSports',
                year=sport.start_time.year,  # type: ignore[attr-defined]
                month=sport.start_time.month,  # type: ignore[attr-defined]
            )
        )

    @workoutSports.route('/delete/<int:sport_id>')
    @login_required
    def delete(sport_id: int):
        sport = get_workout_sport_by_id(sport_id)

        if sport is None:
            abort(404)

        gpxService.delete_gpx(sport, current_user.id)

        LOGGER.debug(f'Deleted workout sport: {sport}')
        db.session.delete(sport)
        db.session.commit()

        return redirect(url_for('sports.listSports'))

    return workoutSports
