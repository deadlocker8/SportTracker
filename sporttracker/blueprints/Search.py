import logging
from itertools import groupby

from flask import Blueprint, render_template, request
from flask_babel import format_datetime
from flask_login import login_required, current_user

from sporttracker.blueprints.Sports import DistanceSportModel, FitnessSportModel
from sporttracker.logic import Constants
from sporttracker.logic.QuickFilterState import get_quick_filter_state_from_session
from sporttracker.logic.model.Sport import Sport
from sporttracker.logic.model.WorkoutType import WorkoutType
from sporttracker.logic.model.User import User
from sporttracker.logic.model.db import db

LOGGER = logging.getLogger(Constants.APP_NAME)


def construct_blueprint():
    search = Blueprint('search', __name__, static_folder='static', url_prefix='/search')

    @search.route('/search')
    @login_required
    def performSearch():
        searchText = request.args.get('searchText')
        pageNumber = request.args.get('pageNumber')

        quickFilterState = get_quick_filter_state_from_session()

        if searchText is None:
            return render_template(
                'search.jinja2',
                results={},
                quickFilterState=quickFilterState,
            )

        searchText = searchText.strip()

        try:
            pageNumberValue = int(pageNumber)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            pageNumberValue = 1

        if pageNumberValue < 1:
            pageNumberValue = 1

        pagination = db.paginate(
            Sport.query.join(User)
            .filter(User.username == current_user.username)
            .filter(Sport.name.icontains(searchText))
            .filter(Sport.type.in_(quickFilterState.get_active_types()))
            .order_by(Sport.start_time.desc()),
            per_page=10,
            page=pageNumberValue,
        )

        results = {
            k: list(g)
            for k, g in groupby(
                pagination.items,
                key=lambda sport: format_datetime(sport.start_time, format='MMMM yyyy'),
            )
        }

        resultModelItems = {}
        for month, sports in results.items():
            itemsPerMonth: list[DistanceSportModel | FitnessSportModel] = []

            for sport in sports:
                if sport.type in WorkoutType.get_distance_sport_types():
                    itemsPerMonth.append(DistanceSportModel.create_from_sport(sport))
                elif sport.type in WorkoutType.get_workout_sport_types():
                    itemsPerMonth.append(FitnessSportModel.create_from_sport(sport))

            resultModelItems[month] = itemsPerMonth

        return render_template(
            'search.jinja2',
            results=resultModelItems,
            pagination=pagination,
            searchText=searchText,
            quickFilterState=quickFilterState,
        )

    return search
