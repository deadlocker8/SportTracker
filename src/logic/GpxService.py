from datetime import datetime

import gpxpy
from gpxpy.gpx import GPX


class GpxService:
    def __init__(self, gpxPath: str):
        self._gpxPath = gpxPath
        self._gpx = self.__parse_gpx(self._gpxPath)

    @staticmethod
    def __parse_gpx(gpxPath: str) -> GPX:
        with open(gpxPath, encoding='utf-8') as f:
            return gpxpy.parse(f)

    def set_name(self, name: str, startTime: datetime) -> None:
        newName = f'{startTime.strftime("%Y-%m-%d")} - {name}'
        self._set_name(newName)

    def _set_name(self, name: str) -> None:
        self._gpx.name = name
        with open(self._gpxPath, 'w', encoding='utf-8') as f:
            f.write(self._gpx.to_xml())
