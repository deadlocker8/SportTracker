import logging
import os
from typing import Any

import requests

from sporttracker.logic import Constants

LOGGER = logging.getLogger(Constants.APP_NAME)


class GpxPreviewImageService:
    def __init__(self, gpxFileName: str, folder: str):
        self._gpxFileName = gpxFileName
        self._folder = folder

        gpxFileNameWithoutExtension = os.path.splitext(self._gpxFileName)[0]
        self._previewImageFileName = f'{gpxFileNameWithoutExtension}.jpg'

    def get_preview_image_path(self) -> str:
        return os.path.join(self._folder, self._previewImageFileName)

    def get_preview_image_file_name(self) -> str:
        return self._previewImageFileName

    def is_image_existing(self) -> bool:
        return os.path.exists(self.get_preview_image_path())

    def generate_image(self, gpxPreviewImageSettings: dict[str, Any]) -> None:
        if not gpxPreviewImageSettings['enabled']:
            return

        if os.path.exists(self.get_preview_image_file_name()):
            return

        try:
            gpxFilePath = os.path.join(self._folder, self._gpxFileName)

            files = {'gpx': open(gpxFilePath, 'rb')}
            response = requests.post(gpxPreviewImageSettings['geoRenderUrl'], files=files)
            response.raise_for_status()

            with open(self.get_preview_image_path(), 'wb') as f:
                f.write(response.content)
        except requests.exceptions.HTTPError as err:
            LOGGER.error(err)
