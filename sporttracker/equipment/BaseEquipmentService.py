from __future__ import annotations

import logging
from datetime import date
from operator import attrgetter
from typing import ClassVar, Generic, TypeVar

from natsort import natsort, natsorted

from sporttracker import Constants
from sporttracker.db import db
from sporttracker.equipment.EquipmentEntity import Equipment
from sporttracker.equipment.EquipmentModel import BaseEquipmentFormModel, EquipmentStatisticModel
from sporttracker.helpers.DateFormats import DATE_FORMAT_DATE
from sporttracker.workout.WorkoutEntity import Workout
from sporttracker.workout.WorkoutType import WorkoutType

LOGGER = logging.getLogger(Constants.APP_NAME)

TEntity = TypeVar('TEntity', bound=Equipment)
TForm = TypeVar('TForm', bound=BaseEquipmentFormModel)


class BaseEquipmentService(Generic[TEntity, TForm]):
    entity_class: ClassVar[type[Equipment]]
    label: ClassVar[str]

    @classmethod
    def add(cls, form: TForm, user_id: int) -> None:
        entity = cls.entity_class(
            workout_type=WorkoutType(form.workout_type),  # type: ignore[call-arg]
            name=form.name,
            purchase_date=cls._parse_purchase_date(form.purchase_date),
            is_active=bool(form.is_active),
            inactive_date=cls._parse_inactive_date(form),
            user_id=user_id,
        )
        cls._apply_extra_fields(entity, form)

        db.session.add(entity)
        db.session.commit()
        LOGGER.debug(f'Saved new {cls.label}: {entity}')

    @classmethod
    def edit(cls, equipment_id: int, form: TForm, user_id: int) -> None:
        entity = cls._get_or_raise(equipment_id, user_id)

        entity.workout_type = WorkoutType(form.workout_type)  # type: ignore[call-arg]
        entity.name = form.name
        entity.purchase_date = cls._parse_purchase_date(form.purchase_date)  # type: ignore[assignment]
        entity.is_active = bool(form.is_active)
        entity.inactive_date = cls._parse_inactive_date(form)  # type: ignore[assignment]
        cls._apply_extra_fields(entity, form)
        db.session.commit()

        LOGGER.debug(f'Updated {cls.label}: {entity}')

    @classmethod
    def delete(cls, equipment_id: int, user_id: int) -> None:
        entity = cls._get_or_raise(equipment_id, user_id)

        LOGGER.debug(f'Deleted {cls.label}: {entity}')
        db.session.delete(entity)
        db.session.commit()

    @classmethod
    def get_by_id(cls, equipment_id: int, user_id: int) -> TEntity | None:
        return (
            cls.entity_class.query.filter(cls.entity_class.user_id == user_id)
            .filter(cls.entity_class.id == equipment_id)
            .first()
        )

    @classmethod
    def get_all_statistic_items_by_workout_type(
        cls, workout_type: WorkoutType, user_id: int
    ) -> list[EquipmentStatisticModel]:
        equipments = (
            cls.entity_class.query.filter(cls.entity_class.user_id == user_id)
            .filter(cls.entity_class.workout_type == workout_type)
            .all()
        )

        items = []
        for equipment in equipments:
            workouts = (
                Workout.query.filter(Workout.user_id == user_id).filter(Workout.equipment.any(id=equipment.id)).all()
            )

            items.append(
                EquipmentStatisticModel(
                    equipment=equipment,
                    number_of_workouts=len(workouts),
                    total_duration=sum(workout.duration for workout in workouts),
                    total_distance=sum(
                        workout.distance
                        for workout in workouts
                        if workout.type in WorkoutType.get_distance_workout_types()
                    ),
                )
            )

        return natsorted(items, alg=natsort.ns.IGNORECASE, key=attrgetter('equipment.name'))

    @classmethod
    def _get_or_raise(cls, equipment_id: int, user_id: int) -> TEntity:
        entity = cls.get_by_id(equipment_id, user_id)

        if entity is None:
            raise ValueError(f'No {cls.label} with ID {equipment_id} found')

        return entity

    @classmethod
    def _apply_extra_fields(cls, entity: TEntity, form: TForm) -> None:
        pass

    @staticmethod
    def _parse_purchase_date(value: str | None) -> date | None:
        if not value:
            return None

        return date.strptime(value, DATE_FORMAT_DATE)

    @staticmethod
    def _parse_inactive_date(form: BaseEquipmentFormModel) -> date | None:
        if form.is_active:
            return None

        if not form.inactive_date:
            return date.today()

        return date.strptime(form.inactive_date, DATE_FORMAT_DATE)
