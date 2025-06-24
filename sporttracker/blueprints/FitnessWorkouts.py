import logging

from flask import Blueprint, render_template, abort, redirect, url_for, request
from flask_login import login_required, current_user
from flask_pydantic import validate

from sporttracker.logic import Constants
from sporttracker.logic.model.CustomWorkoutField import get_custom_fields_by_workout_type_with_values
from sporttracker.logic.model.FitnessWorkoutCategory import (
    FitnessWorkoutCategoryType,
)
from sporttracker.logic.model.Participant import get_participants
from sporttracker.logic.model.PlannedTour import get_planned_tours
from sporttracker.logic.model.Workout import get_workout_names_by_type
from sporttracker.logic.service.FitnessWorkoutService import (
    FitnessWorkoutFormModel,
    FitnessWorkoutService,
)

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint(fitnessWorkoutService: FitnessWorkoutService):
    fitnessWorkouts = Blueprint('fitnessWorkouts', __name__, static_folder='static', url_prefix='/fitnessWorkouts')

    @fitnessWorkouts.route('/post', methods=['POST'])
    @login_required
    @validate()
    def addPost(form: FitnessWorkoutFormModel):
        participant_ids = [int(item) for item in request.form.getlist('participants')]
        fitness_workout_categories = [
            FitnessWorkoutCategoryType(item)  # type: ignore[call-arg]
            for item in request.form.getlist('fitness_workout_categories')
        ]

        workout = fitnessWorkoutService.add_workout(
            form_model=form,
            participant_ids=participant_ids,
            fitness_workout_categories=fitness_workout_categories,
            user_id=current_user.id,
        )

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
        workout = fitnessWorkoutService.get_fitness_workout_by_id(workout_id, current_user.id)

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

        return render_template(
            f'workouts/workout{workout.type.name.capitalize()}Form.jinja2',
            workout=workoutModel,
            workout_id=workout_id,
            customFields=get_custom_fields_by_workout_type_with_values(workout.type),
            participants=get_participants(),
            workoutNames=get_workout_names_by_type(workout.type),
            plannedTours=get_planned_tours([workout.type]),
        )

    @fitnessWorkouts.route('/edit/<int:workout_id>', methods=['POST'])
    @login_required
    @validate()
    def editPost(workout_id: int, form: FitnessWorkoutFormModel):
        try:
            participant_ids = [int(item) for item in request.form.getlist('participants')]
            fitness_workout_categories = [
                FitnessWorkoutCategoryType(item)  # type: ignore[call-arg]
                for item in request.form.getlist('fitness_workout_categories')
            ]

            workout = fitnessWorkoutService.edit_workout(
                workout_id=workout_id,
                form_model=form,
                participant_ids=participant_ids,
                fitness_workout_categories=fitness_workout_categories,
                user_id=current_user.id,
            )

            return redirect(
                url_for(
                    'workouts.listWorkouts',
                    year=workout.start_time.year,  # type: ignore[attr-defined]
                    month=workout.start_time.month,  # type: ignore[attr-defined]
                )
            )
        except ValueError:
            abort(404)

    @fitnessWorkouts.route('/delete/<int:workout_id>')
    @login_required
    def delete(workout_id: int):
        try:
            fitnessWorkoutService.delete_workout_by_id(workout_id, current_user.id)
            return redirect(url_for('workouts.listWorkouts'))
        except ValueError:
            abort(404)

    return fitnessWorkouts
