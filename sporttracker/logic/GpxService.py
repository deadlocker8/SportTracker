import logging
import math
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


@dataclass(frozen=True)
class VisitedTile:
    x: int
    y: int


@dataclass
class GpxMetaInfo:
    distance: float
    elevationExtremes: ElevationExtremes
    uphillDownhill: UphillDownhill
    visitedTiles: set[VisitedTile]


class GpxService:
    def __init__(self, gpxPath: str, baseZoomLevel: int) -> None:
        self._gpxPath = gpxPath
        self._baseZoomLevel = baseZoomLevel
        self._gpx = self.__parse_gpx(self._gpxPath)

    @staticmethod
    def __parse_gpx(gpxPath: str) -> GPX:
        LOGGER.debug(f'Parse gpx "{gpxPath}"')
        with open(gpxPath, encoding='utf-8') as f:
            return gpxpy.parse(f)

    def join_tracks_and_segments(self) -> str:
        self.__join_tracks(self._gpx)
        return self._gpx.to_xml(prettyprint=False)

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

    def __get_length(self) -> float:
        return self._gpx.length_2d()

    def __get_elevation_extremes(self) -> ElevationExtremes:
        elevationExtremes = self._gpx.get_elevation_extremes()
        minimum = elevationExtremes.minimum
        maximum = elevationExtremes.maximum
        if minimum is None or maximum is None:
            return ElevationExtremes(None, None)

        return ElevationExtremes(int(minimum), int(maximum))

    def __get_uphill_downhill(self) -> UphillDownhill:
        uphillDownhill = self._gpx.get_uphill_downhill()
        uphill = uphillDownhill.uphill
        downhill = uphillDownhill.downhill
        if uphill is None or downhill is None:
            return UphillDownhill(None, None)

        return UphillDownhill(int(uphill), int(downhill))

    def __get_visited_tiles(self) -> set[VisitedTile]:
        visitedTiles = set()

        numberOfPoints = self._gpx.get_points_no()
        for track in self._gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    visitedTiles.add(
                        self.__convertCoordinatesToTilePosition(
                            point.latitude, point.longitude, self._baseZoomLevel
                        )
                    )

        LOGGER.debug(
            f'{numberOfPoints} points in gpx track resulted in {len(visitedTiles)} distinct tiles'
        )
        return visitedTiles

    @staticmethod
    def __convertCoordinatesToTilePosition(
        lat_deg: float, lon_deg: float, zoom: int
    ) -> VisitedTile:
        lat_rad = math.radians(lat_deg)
        n = 1 << zoom
        x = int((lon_deg + 180.0) / 360.0 * n)
        y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
        return VisitedTile(x, y)

    def get_meta_info(self) -> GpxMetaInfo:
        return GpxMetaInfo(
            self.__get_length(),
            self.__get_elevation_extremes(),
            self.__get_uphill_downhill(),
            self.__get_visited_tiles(),
        )


class CachedGpxService:
    def __init__(self, baseZoomLevel: int) -> None:
        self._gpxCache: dict[str, GpxMetaInfo] = {}
        self._baseZoomLevel = baseZoomLevel

    def get_base_zoom_level(self):
        return self._baseZoomLevel

    def get_meta_info(self, gpxPath: str) -> GpxMetaInfo:
        if gpxPath not in self._gpxCache:
            gpxService = GpxService(gpxPath, self._baseZoomLevel)
            gpxMetaInfo = gpxService.get_meta_info()
            self._gpxCache[gpxPath] = gpxMetaInfo
            LOGGER.debug(f'Added gpx cache entry for "{gpxPath}"')

        return self._gpxCache[gpxPath]

    def invalidate_cache_entry(self, gpxPath: str) -> None:
        if gpxPath in self._gpxCache:
            LOGGER.debug(f'Invalidated gpx cache entry for "{gpxPath}"')
            del self._gpxCache[gpxPath]
