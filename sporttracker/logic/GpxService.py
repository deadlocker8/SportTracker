import logging
from dataclasses import dataclass

import gpxpy
from gpxpy.gpx import GPX, GPXTrack

from sporttracker.logic import Constants

LOGGER = logging.getLogger(Constants.APP_NAME)


@dataclass
class ElevationExtremes:
    minimum: int | None
    maximum: int | None


@dataclass
class UphillDownhill:
    uphill: int | None
    downhill: int | None


@dataclass
class GpxMetaInfo:
    distance: float
    elevationExtremes: ElevationExtremes
    uphillDownhill: UphillDownhill


class GpxService:
    def __init__(self, gpxPath: str):
        self._gpxPath = gpxPath
        self._gpx = self.__parse_gpx(self._gpxPath)

    @staticmethod
    def __parse_gpx(gpxPath: str) -> GPX:
        LOGGER.debug(f'Parse gpx "{gpxPath}"')
        with open(gpxPath, encoding='utf-8') as f:
            return gpxpy.parse(f)

    def join_tracks_and_segments(self) -> str:
        self.__join_tracks(self._gpx)
        return self._gpx.to_xml(prettyprint=False)

    def get_length(self) -> float:
        return self._gpx.length_2d()

    def get_elevation_extremes(self) -> ElevationExtremes:
        elevationExtremes = self._gpx.get_elevation_extremes()
        minimum = elevationExtremes.minimum
        maximum = elevationExtremes.maximum
        if minimum is None or maximum is None:
            return ElevationExtremes(None, None)

        return ElevationExtremes(int(minimum), int(maximum))

    def get_uphill_downhill(self) -> UphillDownhill:
        uphillDownhill = self._gpx.get_uphill_downhill()
        uphill = uphillDownhill.uphill
        downhill = uphillDownhill.downhill
        if uphill is None or downhill is None:
            return UphillDownhill(None, None)

        return UphillDownhill(int(uphill), int(downhill))

    def get_meta_info(self) -> GpxMetaInfo:
        return GpxMetaInfo(
            self.get_length(), self.get_elevation_extremes(), self.get_uphill_downhill()
        )

    @staticmethod
    def __join_tracks(gpx: GPX) -> None:
        joinedTrack = gpxpy.gpx.GPXTrack()
        numberOfTracks = len(gpx.tracks)
        for track in gpx.tracks:
            joinedTrack.segments.extend(track.segments)

        if numberOfTracks > 1:
            LOGGER.debug(f'Joined {numberOfTracks} tracks')

        gpx.tracks.clear()
        gpx.tracks.append(joinedTrack)

        GpxService.__join_track_segments(joinedTrack)

    @staticmethod
    def __join_track_segments(track: GPXTrack) -> None:
        joinedSegment = gpxpy.gpx.GPXTrackSegment()

        numberOfSegments = len(track.segments)
        for segment in track.segments:
            for point in segment.points:
                joinedSegment.points.append(point)

        if numberOfSegments > 1:
            LOGGER.debug(f'Joined {numberOfSegments} segments')
            track.segments.clear()
            track.segments.append(joinedSegment)
