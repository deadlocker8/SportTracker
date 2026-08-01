import logging
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, abort
from flask_login import login_required, current_user
from flask_pydantic import validate
from pydantic import BaseModel

from sporttracker import Constants
from sporttracker.bodyWeight.BodyWeightService import BmiCategory, BodyWeightService
from sporttracker.helpers import DateFormats

LOGGER = logging.getLogger(Constants.APP_NAME)


class BodyWeightFormModel(BaseModel):
    date: str
    time: str
    weight: float  # kg

    def calculate_date(self) -> datetime:
        return datetime.strptime(f'{self.date} {self.time}', DateFormats.DATE_FORMAT_DATE_TIME)

    def calculate_weight_in_grams(self) -> int:
        return int(round(self.weight * 1000))


def construct_blueprint():
    bodyWeight = Blueprint('bodyWeight', __name__, static_folder='static', url_prefix='/bodyWeight')

    @bodyWeight.route('/', methods=['GET'])
    @login_required
    def listBodyWeight():
        entries = BodyWeightService.get_entries_with_difference(current_user.id)
        averageWeight, minWeight, maxWeight = BodyWeightService.get_average_and_min_and_max(current_user.id)
        latestWeight = entries[0].weight if entries else None
        latestBmi = BodyWeightService.calculate_bmi(latestWeight, current_user.height)
        bmiCategory = BmiCategory.get_bmi_category(latestBmi) if latestBmi is not None else None

        chartDates = []
        chartValues = []
        for entry in reversed(entries):
            chartDates.append(entry.entry_datetime.isoformat())
            chartValues.append(round(entry.weight / 1000, 2))

        return render_template(
            'bodyWeight/bodyWeight.jinja2',
            entries=entries,
            latestWeight=latestWeight,
            averageWeight=averageWeight,
            minWeight=minWeight,
            maxWeight=maxWeight,
            chartDataBodyWeight={'dates': chartDates, 'values': chartValues},
            latestBmi=latestBmi,
            bmiCategory=bmiCategory,
            bmiCategories=list(BmiCategory),
            bmiScaleMax=BodyWeightService.BMI_SCALE_MAX,
        )

    @bodyWeight.route('/add', methods=['GET'])
    @login_required
    def add():
        return render_template(
            'bodyWeight/bodyWeightForm.jinja2',
            today=datetime.now().strftime(DateFormats.DATE_FORMAT_DATE),
        )

    @bodyWeight.route('/post', methods=['POST'])
    @login_required
    @validate()
    def addPost(form: BodyWeightFormModel):
        BodyWeightService.add_body_weight_entry(
            entry_datetime=form.calculate_date(),
            weight=form.calculate_weight_in_grams(),
            user_id=current_user.id,
        )

        LOGGER.debug(f'Saved new body weight entry for user: {current_user.id}')
        return redirect(url_for('bodyWeight.listBodyWeight'))

    @bodyWeight.route('/edit/<int:entry_id>', methods=['GET'])
    @login_required
    def edit(entry_id: int):
        entry = BodyWeightService.get_body_weight_entry_by_id(entry_id, current_user.id)
        if entry is None:
            abort(404)

        form = BodyWeightFormModel(
            date=entry.get_date(),
            time=entry.get_time(),
            weight=round(entry.weight / 1000, 2),
        )
        return render_template('bodyWeight/bodyWeightForm.jinja2', entry=form, entry_id=entry_id)

    @bodyWeight.route('/edit/<int:entry_id>', methods=['POST'])
    @login_required
    @validate()
    def editPost(entry_id: int, form: BodyWeightFormModel):
        entry = BodyWeightService.get_body_weight_entry_by_id(entry_id, current_user.id)
        if entry is None:
            abort(404)

        BodyWeightService.update_body_weight_entry(entry, form.calculate_date(), form.calculate_weight_in_grams())

        LOGGER.debug(f'Updated body weight entry: {entry}')
        return redirect(url_for('bodyWeight.listBodyWeight'))

    @bodyWeight.route('/delete/<int:entry_id>', methods=['GET'])
    @login_required
    def delete(entry_id: int):
        entry = BodyWeightService.get_body_weight_entry_by_id(entry_id, current_user.id)
        if entry is None:
            abort(404)

        LOGGER.debug(f'Deleted body weight entry: {entry}')
        BodyWeightService.delete_body_weight_entry(entry)

        return redirect(url_for('bodyWeight.listBodyWeight'))

    return bodyWeight
