import logging
import os
import tempfile
from typing import Any

import requests

from sporttracker.logic import Constants

LOGGER = logging.getLogger(Constants.APP_NAME)


class GpxPreviewImageService:
    def __init__(self, gpxFileName: str, gpxService) -> None:
        self._gpxFileName = gpxFileName
        self._gpxService = gpxService

        self._previewImageFileName = f'{self._gpxFileName}.jpg'

    def get_preview_image_path(self) -> str:
        return os.path.join(self._gpxService.get_folder_path(self._gpxFileName), self._previewImageFileName)

    def is_image_existing(self) -> bool:
        return os.path.exists(self.get_preview_image_path())

    def generate_image(self, gpxPreviewImageSettings: dict[str, Any]) -> None:
        if not gpxPreviewImageSettings['enabled']:
            return

        if os.path.exists(self.get_preview_image_path()):
            return

        try:
            with tempfile.TemporaryDirectory() as tempDirectory:
                tempGpxFilePath = os.path.join(tempDirectory, f'{self._gpxFileName}.gpx')
                with open(tempGpxFilePath, 'wb') as tempGpxFile:
                    tempGpxFile.write(self._gpxService.get_gpx_content(self._gpxFileName))

                with open(tempGpxFilePath, 'rb') as fd:
                    files = {'gpx': fd}
                    response = requests.post(gpxPreviewImageSettings['geoRenderUrl'], files=files)
                    response.raise_for_status()

                    with open(self.get_preview_image_path(), 'wb') as f:
                        f.write(response.content)
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
            LOGGER.error(err)
