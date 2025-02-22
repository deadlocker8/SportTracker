import logging

from flask import Blueprint, render_template, abort, redirect, url_for, request
from flask_login import login_required, current_user
from flask_pydantic import validate
from pydantic import ConfigDict

from sporttracker.blueprints.Workouts import BaseWorkoutFormModel
from sporttracker.logic import Constants
from sporttracker.logic.model.CustomWorkoutField import CustomWorkoutField
from sporttracker.logic.model.FitnessWorkout import FitnessWorkout, get_fitness_workout_by_id
from sporttracker.logic.model.FitnessWorkoutCategory import (
    update_workout_categories_by_workout_id,
    FitnessWorkoutCategoryType,
)
from sporttracker.logic.model.FitnessWorkoutType import FitnessWorkoutType
from sporttracker.logic.model.Participant import get_participants_by_ids, get_participants
from sporttracker.logic.model.PlannedTour import get_planned_tours
from sporttracker.logic.model.Workout import get_workout_names_by_type
from sporttracker.logic.model.WorkoutType import WorkoutType
from sporttracker.logic.model.db import db

LOGGER = logging.getLogger(Constants.APP_NAME)


class FitnessWorkoutFormModel(BaseWorkoutFormModel):
    fitness_workout_type: str
    fitness_workout_categories: list[str] | str | None | list[FitnessWorkoutCategoryType] = None

    model_config = ConfigDict(
        extra='allow',
    )


def construct_blueprint():
    fitnessWorkouts = Blueprint(
        'fitnessWorkouts', __name__, static_folder='static', url_prefix='/fitnessWorkouts'
    )

    @fitnessWorkouts.route('/post', methods=['POST'])
    @login_required
    @validate()
    def addPost(form: FitnessWorkoutFormModel):
        participantIds = [int(item) for item in request.form.getlist('participants')]
        participants = get_participants_by_ids(participantIds)

        workout = FitnessWorkout(
            name=form.name,
            type=WorkoutType(form.type),  # type: ignore[call-arg]
            start_time=form.calculate_start_time(),
            duration=form.calculate_duration(),
            average_heart_rate=form.average_heart_rate,
            custom_fields=form.model_extra,
            user_id=current_user.id,
            participants=participants,
            fitness_workout_type=FitnessWorkoutType(form.fitness_workout_type),  # type: ignore[call-arg]
        )

        LOGGER.debug(f'Saved new workout workout: {workout}')
        db.session.add(workout)
        db.session.commit()

        fitnessWorkoutCategories = [
            FitnessWorkoutCategoryType(item)  # type: ignore[call-arg]
            for item in request.form.getlist('fitness_workout_categories')
        ]
        update_workout_categories_by_workout_id(workout.id, fitnessWorkoutCategories)

        return redirect(
            url_for(
                'workouts.listWorkouts',
                year=workout.start_time.year,  # type: ignore[attr-defined]
                month=workout.start_time.month,  # type: ignore[attr-defined]
            )
        )

    @fitnessWorkouts.route('/edit/<int:workout_id>')
    @login_required
    def edit(workout_id: int):
        workout = get_fitness_workout_by_id(workout_id)

        if workout is None:
            abort(404)

        workoutModel = FitnessWorkoutFormModel(
            name=workout.name,  # type: ignore[arg-type]
            type=workout.type,
            date=workout.start_time.strftime('%Y-%m-%d'),  # type: ignore[attr-defined]
            time=workout.start_time.strftime('%H:%M'),  # type: ignore[attr-defined]
            duration_hours=workout.duration // 3600,
            duration_minutes=workout.duration % 3600 // 60,
            duration_seconds=workout.duration % 3600 % 60,
            average_heart_rate=workout.average_heart_rate,
            participants=[str(item.id) for item in workout.participants],
            fitness_workout_categories=workout.get_workout_categories(),
            fitness_workout_type=workout.fitness_workout_type,
            **workout.custom_fields,
        )

        customFields = (
            CustomWorkoutField.query.filter(CustomWorkoutField.user_id == current_user.id)
            .filter(CustomWorkoutField.workout_type == workout.type)
            .all()
        )

        return render_template(
            f'workouts/workout{workout.type.name.capitalize()}Form.jinja2',
            workout=workoutModel,
            workout_id=workout_id,
            customFields=customFields,
            participants=get_participants(),
            workoutNames=get_workout_names_by_type(workout.type),
            plannedTours=get_planned_tours([workout.type]),
        )

    @fitnessWorkouts.route('/edit/<int:workout_id>', methods=['POST'])
    @login_required
    @validate()
    def editPost(workout_id: int, form: FitnessWorkoutFormModel):
        workout = get_fitness_workout_by_id(workout_id)

        if workout is None:
            abort(404)

        workout.name = form.name  # type: ignore[assignment]
        workout.start_time = form.calculate_start_time()  # type: ignore[assignment]
        workout.duration = form.calculate_duration()  # type: ignore[assignment]
        workout.average_heart_rate = form.average_heart_rate  # type: ignore[assignment]
        participantIds = [int(item) for item in request.form.getlist('participants')]
        workout.participants = get_participants_by_ids(participantIds)
        workout.fitness_workout_type = (
            None
            if form.fitness_workout_type is None
            else FitnessWorkoutType(form.fitness_workout_type)  # type: ignore[call-arg]
        )

        workout.custom_fields = form.model_extra

        fitnessWorkoutCategories = [
            FitnessWorkoutCategoryType(item)  # type: ignore[call-arg]
            for item in request.form.getlist('fitness_workout_categories')
        ]
        update_workout_categories_by_workout_id(workout.id, fitnessWorkoutCategories)

        db.session.commit()

        LOGGER.debug(f'Updated workout workout: {workout}')

        return redirect(
            url_for(
                'workouts.listWorkouts',
                year=workout.start_time.year,  # type: ignore[attr-defined]
                month=workout.start_time.month,  # type: ignore[attr-defined]
            )
        )

    @fitnessWorkouts.route('/delete/<int:workout_id>')
    @login_required
    def delete(workout_id: int):
        workout = get_fitness_workout_by_id(workout_id)

        if workout is None:
            abort(404)

        LOGGER.debug(f'Deleted workout workout: {workout}')
        db.session.delete(workout)
        db.session.commit()

        return redirect(url_for('workouts.listWorkouts'))

    return fitnessWorkouts
