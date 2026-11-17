from dataclasses import dataclass
from typing import Any

import flask_babel
from babel.dates import get_month_names as get_babel_month_names
from flask import url_for

from sporttracker.equipment.EquipmentModel import EquipmentSelectionWorkoutTypeGroupModel
from sporttracker.user.ParticipantEntity import Participant


@dataclass
class SearchParameters:
    searchText: str
    availableYears: list[int]
    participants: list[Participant]
    isParticipantFilterActive: bool
    equipmentGroupsByWorkoutType: list[EquipmentSelectionWorkoutTypeGroupModel]
    isEquipmentFilterActive: bool
    selectedEquipmentIds: list[int]
    selectedYear: int | None
    selectedMonth: int | None
    selectedParticipantIds: list[int]
    distanceMin: int | None
    distanceMax: int | None

    @staticmethod
    def get_month_names() -> list[str]:
        return list(get_babel_month_names(width='wide', locale=flask_babel.get_locale()).values())

    def build_url(self, pageNumber: int | None = None, includeFilters: bool = True) -> str:
        params: dict[str, Any] = {}

        if self.searchText:
            params['searchText'] = self.searchText

        if includeFilters:
            if self.selectedYear is not None:
                params['year'] = self.selectedYear

            if self.selectedMonth is not None:
                params['month'] = self.selectedMonth

            if self.distanceMin is not None:
                params['distanceMin'] = self.distanceMin

            if self.distanceMax is not None:
                params['distanceMax'] = self.distanceMax

            if self.isParticipantFilterActive:
                params['participantsFilterActive'] = '1'
                params['participants'] = self.selectedParticipantIds

            params['equipmentFilterActive'] = '1'
            if self.isEquipmentFilterActive:
                params['equipment_ids'] = self.selectedEquipmentIds
            else:
                params['allEquipment'] = '1'

        if pageNumber is not None:
            params['pageNumber'] = pageNumber

        return url_for('search.performSearch', **params)
