import logging
import os

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
