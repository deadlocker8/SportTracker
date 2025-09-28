from sporttracker.monthGoal.MonthGoalEntity import (
    MonthGoalCount,
    MonthGoalDistance,
    MonthGoalDuration,
    MonthGoalSummary,
)
from sporttracker.user.UserEntity import User
from sporttracker.workout.WorkoutType import WorkoutType


class MonthGoalService:
    @staticmethod
    def get_month_goal_count_by_id(goal_id: int, user_id: int) -> MonthGoalCount | None:
        return MonthGoalCount.query.join(User).filter(User.id == user_id).filter(MonthGoalCount.id == goal_id).first()

    @staticmethod
    def get_month_goal_distance_by_id(goal_id: int, user_id: int) -> MonthGoalDistance | None:
        return (
            MonthGoalDistance.query.join(User)
            .filter(User.id == user_id)
            .filter(MonthGoalDistance.id == goal_id)
            .first()
        )

    @staticmethod
    def get_month_goal_duration_by_id(goal_id: int, user_id: int) -> MonthGoalDuration | None:
        return (
            MonthGoalDuration.query.join(User)
            .filter(User.id == user_id)
            .filter(MonthGoalDuration.id == goal_id)
            .first()
        )

    @staticmethod
    def get_goal_summaries_by_year_and_month_and_types(
        year: int, month: int, workoutTypes: list[WorkoutType], user_id: int
    ) -> list[MonthGoalSummary]:
        goalsDistance = (
            MonthGoalDistance.query.join(User)
            .filter(User.id == user_id)
            .filter(MonthGoalDistance.year == year)
            .filter(MonthGoalDistance.month == month)
            .filter(MonthGoalDistance.type.in_(workoutTypes))
            .all()
        )
        goalsCount = (
            MonthGoalCount.query.join(User)
            .filter(User.id == user_id)
            .filter(MonthGoalCount.year == year)
            .filter(MonthGoalCount.month == month)
            .filter(MonthGoalCount.type.in_(workoutTypes))
            .all()
        )
        goalsDuration = (
            MonthGoalDuration.query.join(User)
            .filter(User.id == user_id)
            .filter(MonthGoalDuration.year == year)
            .filter(MonthGoalDuration.month == month)
            .filter(MonthGoalDuration.type.in_(workoutTypes))
            .all()
        )

        return [goal.get_summary() for goal in goalsDistance + goalsCount + goalsDuration]

    @staticmethod
    def get_goal_summaries_for_completed_goals(
        year: int, month: int, workoutTypes: list[WorkoutType], user_id: int
    ) -> list[MonthGoalSummary]:
        goals = MonthGoalService.get_goal_summaries_by_year_and_month_and_types(year, month, workoutTypes, user_id)
        return [g for g in goals if g.percentage >= 100.0]

    @staticmethod
    def get_goal_summaries_new_completed(
        year: int, month: int, workoutTypes: list[WorkoutType], user_id: int, previous_completed: list[MonthGoalSummary]
    ) -> list[MonthGoalSummary]:
        currentCompleted = MonthGoalService.get_goal_summaries_for_completed_goals(year, month, workoutTypes, user_id)

        return [
            g
            for g in currentCompleted
            if not MonthGoalService.__is_part_of_previous_completed_goals(g, previous_completed)
        ]

    @staticmethod
    def __is_part_of_previous_completed_goals(
        month_goal_summary: MonthGoalSummary, previous_completed: list[MonthGoalSummary]
    ) -> bool:
        previousCompletedIdsWithSameType = [
            g.id
            for g in previous_completed
            if g.type_name == month_goal_summary.type_name  # type: ignore[attr-defined]
        ]
        return month_goal_summary.id in previousCompletedIdsWithSameType
