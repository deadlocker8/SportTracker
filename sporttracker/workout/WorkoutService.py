from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import extract


if TYPE_CHECKING:
    pass

from sporttracker import Constants

LOGGER = logging.getLogger(Constants.APP_NAME)


class WorkoutService:
    @staticmethod
    def get_available_years(userId) -> list[int]:
        from sporttracker.workout.WorkoutEntity import Workout

        year = extract('year', Workout.start_time)

        rows = (
            Workout.query.with_entities(year.label('year'))
            .filter(Workout.user_id == userId)
            .group_by(year)
            .order_by(year)
            .first()
        )

        if rows is None:
            return [datetime.now().year]

        firstYear = int(rows[0])
        return list(range(firstYear, datetime.now().year + 1))
