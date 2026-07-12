import logging
import os
from typing import Any

from sporttracker import Constants
from sporttracker.gpx.PreviewImageRenderer import render_preview_image

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
            gpx_content = self._gpxService.get_gpx_content(self._gpxFileName)
            render_preview_image(gpx_content, self.get_preview_image_path(), gpxPreviewImageSettings)
        except Exception as err:
            LOGGER.exception(err)
