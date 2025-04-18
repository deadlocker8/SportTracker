import logging

from pydantic import ConfigDict

from sporttracker.api.FormModels import FitnessWorkoutApiFormModel
from sporttracker.blueprints.Workouts import BaseWorkoutFormModel
from sporttracker.logic import Constants
from sporttracker.logic.model.DistanceWorkout import DistanceWorkout
from sporttracker.logic.model.FitnessWorkout import FitnessWorkout
from sporttracker.logic.model.FitnessWorkoutCategory import (
    FitnessWorkoutCategoryType,
    update_workout_categories_by_workout_id,
)
from sporttracker.logic.model.FitnessWorkoutType import FitnessWorkoutType
from sporttracker.logic.model.Participant import get_participants_by_ids
from sporttracker.logic.model.WorkoutType import WorkoutType
from sporttracker.logic.model.db import db

LOGGER = logging.getLogger(Constants.APP_NAME)


class FitnessWorkoutFormModel(BaseWorkoutFormModel):
    fitness_workout_type: str
    fitness_workout_categories: list[str] | str | None | list[FitnessWorkoutCategoryType] = None

    model_config = ConfigDict(
        extra='allow',
    )


class FitnessWorkoutService:
    def add_workout(
        self,
        form_model: FitnessWorkoutFormModel,
        participant_ids: list[int],
        fitness_workout_categories: list[FitnessWorkoutCategoryType],
        user_id: int,
    ) -> DistanceWorkout:
        participants = get_participants_by_ids(participant_ids)

        workout = FitnessWorkout(
            name=form_model.name,
            type=WorkoutType(form_model.type),  # type: ignore[call-arg]
            start_time=form_model.calculate_start_time(),
            duration=form_model.calculate_duration(),
            average_heart_rate=form_model.average_heart_rate,
            custom_fields=form_model.model_extra,
            user_id=user_id,
            participants=participants,
            fitness_workout_type=FitnessWorkoutType(form_model.fitness_workout_type),  # type: ignore[call-arg]
        )

        db.session.add(workout)
        db.session.commit()

        update_workout_categories_by_workout_id(workout.id, fitness_workout_categories)

        LOGGER.debug(f'Saved new fitness workout: {workout}')
        return workout

    def add_workout_via_api(
        self,
        form_model: FitnessWorkoutApiFormModel,
        fitness_workout_categories: list[FitnessWorkoutCategoryType],
        user_id: int,
    ) -> DistanceWorkout:
        participants = get_participants_by_ids(form_model.participants)

        workout = FitnessWorkout(
            name=form_model.name,
            type=WorkoutType(form_model.workout_type),  # type: ignore[call-arg]
            start_time=form_model.calculate_start_time(),
            duration=form_model.duration,
            average_heart_rate=form_model.average_heart_rate,
            custom_fields={} if form_model.custom_fields is None else form_model.custom_fields,
            user_id=user_id,
            participants=participants,
            fitness_workout_type=FitnessWorkoutType(form_model.fitness_workout_type),  # type: ignore[call-arg]
        )

        db.session.add(workout)
        db.session.commit()

        update_workout_categories_by_workout_id(workout.id, fitness_workout_categories)

        LOGGER.debug(f'Saved new fitness workout: {workout}')
        return workout

    def delete_workout_by_id(self, workout_id: int, user_id: int) -> None:
        workout = self.get_fitness_workout_by_id(workout_id, user_id)

        if workout is None:
            raise ValueError(f'No fitness workout with ID {workout_id} found')

        db.session.delete(workout)
        db.session.commit()

        LOGGER.debug(f'Deleted fitness workout: {workout}')

    def edit_workout(
        self,
        workout_id: int,
        form_model: FitnessWorkoutFormModel,
        participant_ids: list[int],
        fitness_workout_categories: list[FitnessWorkoutCategoryType],
        user_id: int,
    ) -> DistanceWorkout:
        workout = self.get_fitness_workout_by_id(workout_id, user_id)

        if workout is None:
            raise ValueError(f'No fitness workout with ID {workout_id} found')

        workout.name = form_model.name  # type: ignore[assignment]
        workout.start_time = form_model.calculate_start_time()  # type: ignore[assignment]
        workout.duration = form_model.calculate_duration()  # type: ignore[assignment]
        workout.average_heart_rate = form_model.average_heart_rate  # type: ignore[assignment]
        workout.participants = get_participants_by_ids(participant_ids)
        workout.fitness_workout_type = (
            None if form_model.fitness_workout_type is None else FitnessWorkoutType(form_model.fitness_workout_type)  # type: ignore[call-arg]
        )

        workout.custom_fields = form_model.model_extra

        update_workout_categories_by_workout_id(workout.id, fitness_workout_categories)

        db.session.commit()

        LOGGER.debug(f'Updated fitness workout: {workout}')
        return workout

    @staticmethod
    def get_fitness_workout_by_id(workout_id: int, user_id: int) -> FitnessWorkout | None:
        return (
            FitnessWorkout.query.filter(FitnessWorkout.user_id == user_id)
            .filter(FitnessWorkout.id == workout_id)
            .first()
        )
