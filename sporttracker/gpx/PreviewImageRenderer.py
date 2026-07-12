import logging
import os
import tempfile
from typing import Any

import requests

from sporttracker import Constants

LOGGER = logging.getLogger(Constants.APP_NAME)


def render_preview_image(
    gpx_content: bytes, output_image_path: str, gpx_preview_image_settings: dict[str, Any]
) -> None:
    with tempfile.TemporaryDirectory() as temp_directory:
        temp_gpx_file_path = os.path.join(temp_directory, 'preview.gpx')
        with open(temp_gpx_file_path, 'wb') as temp_gpx_file:
            temp_gpx_file.write(gpx_content)

        with open(temp_gpx_file_path, 'rb') as fd:
            files = {'file': fd}
            data = {
                'width': gpx_preview_image_settings['width'],
                'height': gpx_preview_image_settings['height'],
                'line_width': gpx_preview_image_settings['lineWidth'],
                'line_color': gpx_preview_image_settings['lineColor'],
                'basemap': gpx_preview_image_settings['basemap'],
                'dpi': gpx_preview_image_settings['dpi'],
                'padding': gpx_preview_image_settings['padding'],
                'format': gpx_preview_image_settings['format'],
                'quality': gpx_preview_image_settings['quality'],
            }
            timeout = gpx_preview_image_settings['timeout']
            response = requests.post(gpx_preview_image_settings['url'], files=files, data=data, timeout=timeout)
            response.raise_for_status()

            with open(output_image_path, 'wb') as f:
                f.write(response.content)
