import logging
from dataclasses import dataclass
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, abort
from flask_login import login_required, current_user
from flask_pydantic import validate
from pydantic import BaseModel

from sporttracker.logic import Constants
from sporttracker.logic.QuickFilterState import get_quick_filter_state_from_session
from sporttracker.logic.model.PlannedTour import PlannedTour
from sporttracker.logic.model.Track import TrackType
from sporttracker.logic.model.db import db

LOGGER = logging.getLogger(Constants.APP_NAME)


@dataclass
class PlannedTourModel:
    id: int
    name: str
    lastEditDate: datetime
    type: TrackType


class PlannedTourFormModel(BaseModel):
    name: str
    type: str


def construct_blueprint():
    plannedTours = Blueprint(
        'plannedTours', __name__, static_folder='static', url_prefix='/plannedTours'
    )

    @plannedTours.route('/')
    @login_required
    def listPlannedTours():
        quickFilterState = get_quick_filter_state_from_session()

        tours: list[PlannedTour] = (
            PlannedTour.query.filter(PlannedTour.user_id == current_user.id)
            .filter(PlannedTour.type.in_(quickFilterState.get_active_types()))
            .order_by(PlannedTour.name.desc())
            .all()
        )

        plannedTourList: list[PlannedTourModel] = []
        for tour in tours:
            plannedTourList.append(
                PlannedTourModel(
                    id=tour.id,
                    name=tour.name,
                    lastEditDate=tour.last_edit_date,
                    type=tour.type.name,
                )
            )

        return render_template(
            'plannedTours/plannedTours.jinja2',
            plannedTours=plannedTourList,
            quickFilterState=quickFilterState,
        )

    @plannedTours.route('/add')
    @login_required
    def add():
        return render_template('plannedTours/plannedTourForm.jinja2')

    @plannedTours.route('/post', methods=['POST'])
    @login_required
    @validate()
    def addPost(form: PlannedTourFormModel):
        plannedTour = PlannedTour(
            name=form.name,
            type=TrackType(form.type),  # type: ignore[call-arg]
            user_id=current_user.id,
            last_edit_date=datetime.now(),
        )

        LOGGER.debug(f'Saved new planned tour: {plannedTour}')
        db.session.add(plannedTour)
        db.session.commit()

        return redirect(url_for('plannedTours.listPlannedTours'))

    @plannedTours.route('/edit/<int:tour_id>')
    @login_required
    def edit(tour_id: int):
        plannedTour = (
            PlannedTour.query.filter(PlannedTour.user_id == current_user.id)
            .filter(PlannedTour.id == tour_id)
            .first()
        )

        if plannedTour is None:
            abort(404)

        tourModel = PlannedTourModel(
            id=plannedTour.id,
            name=plannedTour.name,
            lastEditDate=plannedTour.last_edit_date,
            type=plannedTour.type.name,
        )

        return render_template(
            'plannedTours/plannedTourForm.jinja2',
            plannedTour=tourModel,
            tour_id=tour_id,
        )

    @plannedTours.route('/edit/<int:tour_id>', methods=['POST'])
    @login_required
    @validate()
    def editPost(tour_id: int, form: PlannedTourFormModel):
        plannedTour = (
            PlannedTour.query.filter(PlannedTour.user_id == current_user.id)
            .filter(PlannedTour.id == tour_id)
            .first()
        )

        if plannedTour is None:
            abort(404)

        plannedTour.type = TrackType(form.type)  # type: ignore[call-arg]
        plannedTour.name = form.name
        plannedTour.user_id = current_user.id
        plannedTour.last_edit_date = datetime.now()

        LOGGER.debug(f'Updated planned tour: {plannedTour}')
        db.session.commit()

        return redirect(url_for('plannedTours.listPlannedTours'))

    @plannedTours.route('/delete/<int:tour_id>')
    @login_required
    def delete(tour_id: int):
        plannedTour = (
            PlannedTour.query.filter(PlannedTour.user_id == current_user.id)
            .filter(PlannedTour.id == tour_id)
            .first()
        )

        if plannedTour is None:
            abort(404)

        LOGGER.debug(f'Deleted planned tour: {plannedTour}')
        db.session.delete(plannedTour)
        db.session.commit()

        return redirect(url_for('plannedTours.listPlannedTours'))

    return plannedTours
