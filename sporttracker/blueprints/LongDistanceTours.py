import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from flask import Blueprint, render_template, request, redirect, url_for, abort
from flask_login import login_required, current_user
from flask_pydantic import validate

from sporttracker.plannedTour.PlannedTourBlueprint import __get_user_models
from sporttracker.logic import Constants
from sporttracker.logic.model.LongDistanceTour import LongDistanceTour
from sporttracker.logic.model.User import get_user_by_id, get_all_users_except_self_and_admin
from sporttracker.logic.model.WorkoutType import WorkoutType
from sporttracker.logic.model.filterStates.QuickFilterState import get_quick_filter_state_by_user
from sporttracker.logic.service.LongDistanceTourService import LongDistanceTourFormModel, LongDistanceTourService
from sporttracker.plannedTour.PlannedTourService import PlannedTourService, PlannedTourModel

LOGGER = logging.getLogger(Constants.APP_NAME)


@dataclass
class SharedUserModel:
    id: int
    name: str


@dataclass
class LongDistanceTourModel:
    id: int
    name: str
    creationDate: datetime
    lastEditDate: datetime
    type: WorkoutType
    sharedUsers: list[str]
    ownerId: str
    ownerName: str
    linkedPlannedTours: list[PlannedTourModel]

    @staticmethod
    def create_from_tour(longDistanceTour: LongDistanceTour) -> 'LongDistanceTourModel':
        return LongDistanceTourModel(
            id=longDistanceTour.id,
            name=longDistanceTour.name,  # type: ignore[arg-type]
            creationDate=longDistanceTour.creation_date,  # type: ignore[arg-type]
            lastEditDate=longDistanceTour.last_edit_date,  # type: ignore[arg-type]
            type=longDistanceTour.type,
            sharedUsers=[str(user.id) for user in longDistanceTour.shared_users],
            ownerId=str(longDistanceTour.user_id),
            ownerName=get_user_by_id(longDistanceTour.user_id).username,
            linkedPlannedTours=[
                PlannedTourModel.create_from_tour(
                    PlannedTourService.get_planned_tour_by_id(p.planned_tour_id),  # type: ignore[arg-type]
                    True,
                )
                for p in longDistanceTour.linked_planned_tours
            ],
        )

    def get_number_of_completed_stages(self) -> int:
        return len([t for t in self.linkedPlannedTours if len(t.linkedWorkouts) > 0])

    def get_total_distance(self) -> float:
        totalDistance = 0.0
        for planned_tour in self.linkedPlannedTours:
            if planned_tour.gpxMetadata is not None:
                totalDistance += planned_tour.gpxMetadata.length

        return totalDistance

    def get_completed_distance(self) -> float:
        completedDistance = 0.0
        for planned_tour in self.linkedPlannedTours:
            if planned_tour.gpxMetadata is None:
                continue

            if len(planned_tour.linkedWorkouts) == 0:
                continue

            completedDistance += planned_tour.gpxMetadata.length

        return completedDistance


def construct_blueprint(
    gpxPreviewImageSettings: dict[str, Any],
    longDistanceTourService: LongDistanceTourService,
) -> Blueprint:
    longDistanceTours = Blueprint(
        'longDistanceTours', __name__, static_folder='static', url_prefix='/longDistanceTours'
    )

    @longDistanceTours.route('/')
    @login_required
    def listLongDistanceTours():
        quickFilterState = get_quick_filter_state_by_user(current_user.id)

        longDistanceTourList = longDistanceTourService.get_long_distance_tours(
            quickFilterState.get_active_distance_workout_types()
        )

        return render_template(
            'longDistanceTours/longDistanceTours.jinja2',
            longDistanceTours=[LongDistanceTourModel.create_from_tour(t) for t in longDistanceTourList],
            quickFilterState=quickFilterState,
            isGpxPreviewImagesEnabled=gpxPreviewImageSettings['enabled'],
        )

    @longDistanceTours.route('/add')
    @login_required
    def add():
        return render_template(
            'longDistanceTours/longDistanceTourForm.jinja2',
            users=__get_user_models(get_all_users_except_self_and_admin()),
            plannedTours=PlannedTourService.get_available_planned_tours(
                get_quick_filter_state_by_user(current_user.id)
            ),
        )

    @longDistanceTours.route('/post', methods=['POST'])
    @login_required
    @validate()
    def addPost(form: LongDistanceTourFormModel):
        shared_user_ids = [int(item) for item in request.form.getlist('sharedUsers')]

        long_distance_tour = longDistanceTourService.add_long_distance_tour(
            form_model=form,
            shared_user_ids=shared_user_ids,
            user_id=current_user.id,
        )

        return redirect(url_for('maps.showLongDistanceTour', tour_id=long_distance_tour.id))

    @longDistanceTours.route('/edit/<int:tour_id>')
    @login_required
    def edit(tour_id: int):
        longDistanceTour = longDistanceTourService.get_long_distance_tour_by_id(tour_id)

        if longDistanceTour is None:
            abort(404)

        tourModel = LongDistanceTourModel.create_from_tour(longDistanceTour)

        return render_template(
            'longDistanceTours/longDistanceTourForm.jinja2',
            longDistanceTour=tourModel,
            tour_id=tour_id,
            users=__get_user_models(get_all_users_except_self_and_admin()),
            plannedTours=PlannedTourService.get_available_planned_tours(
                get_quick_filter_state_by_user(current_user.id)
            ),
        )

    @longDistanceTours.route('/edit/<int:tour_id>', methods=['POST'])
    @login_required
    @validate()
    def editPost(tour_id: int, form: LongDistanceTourFormModel):
        try:
            shared_user_ids = [int(item) for item in request.form.getlist('sharedUsers')]

            long_distance_tour = longDistanceTourService.edit_long_distance_tour(
                tour_id=tour_id,
                form_model=form,
                shared_user_ids=shared_user_ids,
                user_id=current_user.id,
            )

            return redirect(url_for('maps.showLongDistanceTour', tour_id=long_distance_tour.id))
        except ValueError:
            abort(404)

    @longDistanceTours.route('/delete/<int:tour_id>/<int:delete_linked_tours>')
    @login_required
    def delete(tour_id: int, delete_linked_tours: int):
        try:
            longDistanceTourService.delete_long_distance_tour_by_id(tour_id, current_user.id, delete_linked_tours == 1)
            return redirect(url_for('longDistanceTours.listLongDistanceTours'))
        except ValueError:
            abort(404)

    return longDistanceTours
