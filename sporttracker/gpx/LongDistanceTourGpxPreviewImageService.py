import logging
import os
import tempfile
from typing import Any

import requests

from sporttracker import Constants
from sporttracker.longDistanceTour.LongDistanceTourEntity import LongDistanceTour
from sporttracker.plannedTour.PlannedTourService import PlannedTourService

LOGGER = logging.getLogger(Constants.APP_NAME)


class ImageGenerationException(Exception):
    pass


class LongDistanceTourGpxPreviewImageService:
    def __init__(self, longDistanceTour: LongDistanceTour, gpxService) -> None:
        self._longDistanceTour = longDistanceTour
        self._gpxService = gpxService

        self._uniqueName = f'long_distance_tour_{self._longDistanceTour.id}'
        self._previewImageFileName = f'{self._uniqueName}.jpg'

    def get_preview_image_path(self) -> str:
        return os.path.join(self._gpxService.get_folder_path(self._uniqueName), self._previewImageFileName)

    def is_image_existing(self) -> bool:
        return os.path.exists(self.get_preview_image_path())

    def generate_image(self, gpxPreviewImageSettings: dict[str, Any]) -> None:
        try:
            if not gpxPreviewImageSettings['enabled']:
                raise ImageGenerationException()

            os.makedirs(self._gpxService.get_folder_path(self._uniqueName), exist_ok=True)

            linkedPlannedTours = self._longDistanceTour.linked_planned_tours
            gpxFileNames = self.__determine_gpx_file_names(linkedPlannedTours)
            if not gpxFileNames:
                raise ImageGenerationException()

            self.__render_image(gpxFileNames, gpxPreviewImageSettings)
        except ImageGenerationException:
            if os.path.exists(self.get_preview_image_path()):
                try:
                    os.remove(self.get_preview_image_path())
                except Exception as err:
                    LOGGER.error(err)

    @staticmethod
    def __determine_gpx_file_names(linkedPlannedTours):
        gpxFileNames = []
        for linkedPlannedTour in linkedPlannedTours:
            plannedTour = PlannedTourService.get_planned_tour_by_id(linkedPlannedTour.planned_tour_id)
            if plannedTour is None:
                continue

            gpxMetadata = plannedTour.get_gpx_metadata()

            if gpxMetadata is None:
                continue

            gpxFileNames.append(gpxMetadata.gpx_file_name)
        return gpxFileNames

    def __render_image(self, gpxFileNames, gpxPreviewImageSettings):
        try:
            with tempfile.TemporaryDirectory() as tempDirectory:
                tempGpxFilePath = os.path.join(tempDirectory, f'{self._uniqueName}.gpx')
                with open(tempGpxFilePath, 'wb') as tempGpxFile:
                    tempGpxFile.write(self._gpxService.join_multiple_gpx(gpxFileNames))

                with open(tempGpxFilePath, 'rb') as fd:
                    files = {'gpx': fd}
                    response = requests.post(gpxPreviewImageSettings['geoRenderUrl'], files=files)
                    response.raise_for_status()

                    with open(self.get_preview_image_path(), 'wb') as f:
                        f.write(response.content)
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
            LOGGER.error(err)
            raise ImageGenerationException()
