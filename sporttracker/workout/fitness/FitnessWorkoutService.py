import logging

from pydantic import ConfigDict

from sporttracker.achievement.AchievementCalculator import AchievementCalculator
from sporttracker.api.FormModels import FitnessWorkoutApiFormModel
from sporttracker import Constants
from sporttracker.monthGoal.MonthGoalService import MonthGoalService
from sporttracker.notification.NotificationService import NotificationService
from sporttracker.workout.WorkoutModel import BaseWorkoutFormModel
from sporttracker.workout.distance.DistanceWorkoutEntity import DistanceWorkout
from sporttracker.workout.fitness.FitnessWorkoutEntity import FitnessWorkout
from sporttracker.workout.fitness.FitnessWorkoutCategory import (
    FitnessWorkoutCategoryType,
    update_workout_categories_by_workout_id,
)
from sporttracker.workout.fitness.FitnessWorkoutType import FitnessWorkoutType
from sporttracker.user.ParticipantEntity import get_participants_by_ids
from sporttracker.workout.WorkoutType import WorkoutType
from sporttracker.db import db

LOGGER = logging.getLogger(Constants.APP_NAME)


class FitnessWorkoutFormModel(BaseWorkoutFormModel):
    fitness_workout_type: str
    fitness_workout_categories: list[str] | str | None | list[FitnessWorkoutCategoryType] = None

    model_config = ConfigDict(
        extra='allow',
    )


class FitnessWorkoutService:
    def __init__(self, notification_service: NotificationService) -> None:
        self._notification_service = notification_service

    def add_workout(
        self,
        form_model: FitnessWorkoutFormModel,
        participant_ids: list[int],
        fitness_workout_categories: list[FitnessWorkoutCategoryType],
        user_id: int,
    ) -> DistanceWorkout:
        participants = get_participants_by_ids(participant_ids)

        startTime = form_model.calculate_start_time()
        workout = FitnessWorkout(
            name=form_model.name,
            type=WorkoutType(form_model.type),  # type: ignore[call-arg]
            start_time=startTime,
            duration=form_model.calculate_duration(),
            average_heart_rate=form_model.average_heart_rate,
            custom_fields=form_model.model_extra,
            user_id=user_id,
            participants=participants,
            fitness_workout_type=FitnessWorkoutType(form_model.fitness_workout_type),  # type: ignore[call-arg]
        )

        previousLongestDuration = self.get_previous_longest_workout_duration(user_id, workout.type)
        previousCompletedMonthGoals = MonthGoalService.get_goal_summaries_for_completed_goals(
            startTime.year, startTime.month, [workout.type], user_id
        )

        db.session.add(workout)
        db.session.commit()

        update_workout_categories_by_workout_id(workout.id, fitness_workout_categories)

        LOGGER.debug(f'Saved new fitness workout: {workout}')
        self._notification_service.on_duration_workout_updated(user_id, workout, previousLongestDuration)
        self._notification_service.on_check_month_goals(user_id, workout, previousCompletedMonthGoals)
        return workout

    def add_workout_via_api(
        self,
        form_model: FitnessWorkoutApiFormModel,
        fitness_workout_categories: list[FitnessWorkoutCategoryType],
        user_id: int,
    ) -> DistanceWorkout:
        participants = get_participants_by_ids(form_model.participants)

        startTime = form_model.calculate_start_time()
        workout = FitnessWorkout(
            name=form_model.name,
            type=WorkoutType(form_model.workout_type),  # type: ignore[call-arg]
            start_time=startTime,
            duration=form_model.duration,
            average_heart_rate=form_model.average_heart_rate,
            custom_fields={} if form_model.custom_fields is None else form_model.custom_fields,
            user_id=user_id,
            participants=participants,
            fitness_workout_type=FitnessWorkoutType(form_model.fitness_workout_type),  # type: ignore[call-arg]
        )

        previousLongestDuration = self.get_previous_longest_workout_duration(user_id, workout.type)
        previousCompletedMonthGoals = MonthGoalService.get_goal_summaries_for_completed_goals(
            startTime.year, startTime.month, [workout.type], user_id
        )

        db.session.add(workout)
        db.session.commit()

        update_workout_categories_by_workout_id(workout.id, fitness_workout_categories)

        LOGGER.debug(f'Saved new fitness workout: {workout}')
        self._notification_service.on_duration_workout_updated(user_id, workout, previousLongestDuration)
        self._notification_service.on_check_month_goals(user_id, workout, previousCompletedMonthGoals)
        return workout

    def delete_workout_by_id(self, workout_id: int, user_id: int) -> None:
        workout = self.get_fitness_workout_by_id(workout_id, user_id)

        if workout is None:
            raise ValueError(f'No fitness workout with ID {workout_id} found')

        db.session.delete(workout)
        db.session.commit()

        LOGGER.debug(f'Deleted fitness workout: {workout}')
        self._notification_service.on_duration_workout_updated(user_id, workout, None)

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

        startTime = form_model.calculate_start_time()

        previousLongestDuration = self.get_previous_longest_workout_duration(user_id, workout.type)
        previousCompletedMonthGoals = MonthGoalService.get_goal_summaries_for_completed_goals(
            startTime.year, startTime.month, [workout.type], user_id
        )

        workout.name = form_model.name  # type: ignore[assignment]
        workout.start_time = startTime  # type: ignore[assignment]
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
        self._notification_service.on_duration_workout_updated(user_id, workout, previousLongestDuration)
        self._notification_service.on_check_month_goals(user_id, workout, previousCompletedMonthGoals)
        return workout

    @staticmethod
    def get_fitness_workout_by_id(workout_id: int, user_id: int) -> FitnessWorkout | None:
        return (
            FitnessWorkout.query.filter(FitnessWorkout.user_id == user_id)
            .filter(FitnessWorkout.id == workout_id)
            .first()
        )

    @staticmethod
    def get_previous_longest_workout_duration(user_id: int, workout_type: WorkoutType) -> int | None:
        longestWorkouts = AchievementCalculator.get_workouts_with_longest_durations_by_type(user_id, workout_type)
        if not longestWorkouts:
            return None

        longestWorkout = longestWorkouts[0]
        if longestWorkout.workout_id is None:
            return None

        workout = FitnessWorkoutService.get_fitness_workout_by_id(longestWorkout.workout_id, user_id)
        if workout is None:
            return None

        return workout.duration
